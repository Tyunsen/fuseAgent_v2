from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from io import BytesIO

from sqlalchemy import select

from aperag.config import get_sync_session, settings
from aperag.db import models as db_models
from aperag.db.ops import async_db_ops, db_ops
from aperag.exceptions import CollectionNotFoundException
from aperag.mirofish_graph.constants import (
    GRAPH_STATUS_BUILDING,
    GRAPH_STATUS_FAILED,
    GRAPH_STATUS_READY,
    GRAPH_STATUS_UPDATING,
    MIROFISH_GRAPH_ENGINE,
)
from aperag.mirofish_graph.graph_extractor import ChunkGraphExtractor
from aperag.mirofish_graph.graph_identity import graph_key
from aperag.mirofish_graph.helpers import build_graph_status_message, is_mirofish_collection_config
from aperag.mirofish_graph.llm_client import MiroFishLLMClient
from aperag.mirofish_graph.neo4j_graph_backend import Neo4jGraphBackend
from aperag.mirofish_graph.ontology_generator import OntologyGenerator
from aperag.objectstore.base import get_object_store
from aperag.schema.utils import dumpCollectionConfig, parseCollectionConfig
from aperag.schema.view_models import GraphLabelsResponse
from aperag.tasks.utils import cleanup_local_document, parse_document_content
from aperag.utils.utils import utc_now

logger = logging.getLogger(__name__)


@dataclass
class _MiroFishProject:
    project_id: str
    name: str


class MiroFishGraphService:
    def __init__(self) -> None:
        self.db_ops = async_db_ops
        self.sync_db_ops = db_ops

    async def prepare_graph_build(self, user_id: str, collection_id: str) -> int | None:
        async def _operation(session):
            stmt = select(db_models.Collection).where(
                db_models.Collection.id == collection_id,
                db_models.Collection.user == user_id,
                db_models.Collection.status != db_models.CollectionStatus.DELETED,
            )
            result = await session.execute(stmt)
            collection = result.scalars().first()
            if not collection:
                raise CollectionNotFoundException(collection_id)

            config = parseCollectionConfig(collection.config)
            if not is_mirofish_collection_config(config):
                return None

            next_revision = (config.graph_revision or 0) + 1
            has_previous_request = (config.graph_revision or 0) > 0
            has_active_graph = bool(config.active_graph_id)
            next_status = GRAPH_STATUS_BUILDING if not has_previous_request and not has_active_graph else GRAPH_STATUS_UPDATING

            config.graph_revision = next_revision
            config.graph_status = next_status
            config.graph_status_message = build_graph_status_message(
                next_status,
                has_active_graph=has_active_graph,
            )
            config.graph_error = None
            collection.config = dumpCollectionConfig(config)
            session.add(collection)
            await session.flush()
            return next_revision

        return await self.db_ops.execute_with_transaction(_operation)

    def build_graph_for_collection(self, collection_id: str, target_revision: int) -> dict:
        collection = self.sync_db_ops.query_collection_by_id(collection_id)
        if not collection:
            raise CollectionNotFoundException(collection_id)

        config = parseCollectionConfig(collection.config)
        if not is_mirofish_collection_config(config):
            logger.info("Skip MiroFish graph build for non-MiroFish collection %s", collection_id)
            return {"collection_id": collection_id, "skipped": True}

        llm_client = self._build_llm_client(collection, config)
        ontology_generator = OntologyGenerator(llm_client)
        backend = Neo4jGraphBackend(ChunkGraphExtractor(llm_client))

        documents = self._load_confirmed_documents(collection)
        document_sections, document_texts = self._collect_document_texts(collection, documents)
        if not document_sections:
            raise ValueError(f"No confirmed documents are available for collection {collection_id}")

        ontology = ontology_generator.generate(
            document_texts=document_texts,
            simulation_requirement=(collection.description or collection.title or "").strip(),
            additional_context=f"Knowledge base title: {collection.title or collection_id}",
        )

        project = _MiroFishProject(
            project_id=f"{collection.id}:r{target_revision}",
            name=collection.title or collection.id,
        )
        combined_text = "\n\n".join(document_sections)
        graph_data = backend.build_graph(
            project=project,
            text=combined_text,
            ontology=ontology,
            graph_name=f"{collection.title or collection.id} r{target_revision}",
            chunk_size=settings.mirofish_graph_chunk_size,
            chunk_overlap=settings.mirofish_graph_chunk_overlap,
            task_id=f"{collection.id}:{target_revision}",
        )
        active_graph_id = graph_key(project.project_id)

        if not self._finalize_success(collection_id, target_revision, active_graph_id):
            backend.delete_graph(active_graph_id)
            return {"collection_id": collection_id, "stale": True, "graph_id": active_graph_id}

        return {
            "collection_id": collection_id,
            "graph_id": active_graph_id,
            "revision": target_revision,
            "node_count": graph_data.get("node_count", 0),
            "edge_count": graph_data.get("edge_count", 0),
        }

    def handle_build_failure(self, collection_id: str, target_revision: int, error: str) -> None:
        self._finalize_failure(collection_id, target_revision, error)

    async def get_graph_labels(self, user_id: str, collection_id: str) -> GraphLabelsResponse:
        graph_data = await self._load_graph_data(user_id, collection_id)
        labels = sorted(
            {
                self._entity_type_from_node(node)
                for node in graph_data.get("nodes", [])
                if self._entity_type_from_node(node)
            }
        )
        return GraphLabelsResponse(labels=labels)

    async def get_knowledge_graph(
        self,
        user_id: str,
        collection_id: str,
        label: str = "*",
        max_nodes: int = 1000,
    ) -> dict:
        graph_data = await self._load_graph_data(user_id, collection_id)
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        if label and label != "*":
            selected_ids = {
                node["uuid"]
                for node in nodes
                if self._entity_type_from_node(node) == label
            }
            nodes = [node for node in nodes if node["uuid"] in selected_ids]
            edges = [
                edge
                for edge in edges
                if edge["source_node_uuid"] in selected_ids and edge["target_node_uuid"] in selected_ids
            ]

        is_truncated = len(nodes) > max_nodes
        if is_truncated:
            selected_ids = {node["uuid"] for node in nodes[:max_nodes]}
            nodes = nodes[:max_nodes]
            edges = [
                edge
                for edge in edges
                if edge["source_node_uuid"] in selected_ids and edge["target_node_uuid"] in selected_ids
            ]

        return {
            "nodes": [self._map_graph_node(node) for node in nodes],
            "edges": [self._map_graph_edge(edge) for edge in edges],
            "is_truncated": is_truncated,
        }

    async def get_graph_snapshot(self, user_id: str, collection_id: str) -> dict:
        """Return raw graph data with provenance for answer-scoped graph derivation."""
        return await self._load_graph_data(user_id, collection_id)

    async def _load_graph_data(self, user_id: str, collection_id: str) -> dict:
        collection = await self.db_ops.query_collection(user_id, collection_id)
        if not collection:
            raise CollectionNotFoundException(collection_id)

        config = parseCollectionConfig(collection.config)
        if not is_mirofish_collection_config(config):
            raise ValueError(f"Collection {collection_id} is not using the MiroFish graph engine")

        if not config.active_graph_id:
            return {"nodes": [], "edges": []}

        llm_client = self._build_llm_client(collection, config)
        backend = Neo4jGraphBackend(ChunkGraphExtractor(llm_client))
        return await asyncio.to_thread(backend.get_graph_data, config.active_graph_id)

    def _load_confirmed_documents(self, collection: db_models.Collection) -> list[db_models.Document]:
        documents = self.sync_db_ops.query_documents([collection.user], collection.id)
        return [
            document
            for document in documents
            if document.status not in {db_models.DocumentStatus.UPLOADED, db_models.DocumentStatus.EXPIRED, db_models.DocumentStatus.DELETED}
        ]

    def _collect_document_texts(
        self,
        collection: db_models.Collection,
        documents: list[db_models.Document],
    ) -> tuple[list[str], list[str]]:
        sections: list[str] = []
        document_texts: list[str] = []
        for document in documents:
            cached_content = self._read_cached_document_markdown(document)
            if cached_content:
                sections.append(f"=== {document.name} ===\n{cached_content}")
                document_texts.append(cached_content)
                continue

            local_doc = None
            try:
                content, _, local_doc = parse_document_content(document, collection)
                content = (content or "").strip()
                if not content:
                    continue
                sections.append(f"=== {document.name} ===\n{content}")
                document_texts.append(content)
            except Exception as exc:
                logger.warning(
                    "Failed to parse collection document %s for MiroFish graph build: %s",
                    document.id,
                    exc,
                )
            finally:
                if local_doc is not None:
                    cleanup_local_document(local_doc, collection)
        return sections, document_texts

    def _read_cached_document_markdown(self, document: db_models.Document) -> str | None:
        markdown_path = f"{document.object_store_base_path()}/parsed.md"
        obj_store = get_object_store()

        stream = None
        try:
            stream = obj_store.get(markdown_path)
            if stream is None:
                return None

            raw_content = stream.read()
            if isinstance(raw_content, str):
                content = raw_content
            elif isinstance(raw_content, bytes):
                content = raw_content.decode("utf-8")
            else:
                content = BytesIO(raw_content).read().decode("utf-8")

            content = content.strip()
            if content:
                logger.info("Using cached parsed markdown for MiroFish graph build: %s", document.id)
                return content
        except Exception as exc:
            logger.warning(
                "Failed to read cached parsed markdown for document %s: %s",
                document.id,
                exc,
            )
        finally:
            if stream is not None:
                close = getattr(stream, "close", None)
                if callable(close):
                    close()

        return None

    def _build_llm_client(self, collection: db_models.Collection, config) -> MiroFishLLMClient:
        completion = config.completion
        if not completion or not completion.model or not completion.model_service_provider:
            raise ValueError(f"Collection {collection.id} does not have a valid completion model for MiroFish graph build")

        api_key = self.sync_db_ops.query_provider_api_key(
            completion.model_service_provider,
            user_id=collection.user,
            need_public=True,
        )
        provider = self.sync_db_ops.query_llm_provider_by_name(
            completion.model_service_provider,
            user_id=collection.user,
        )
        if not api_key:
            raise ValueError(f"Provider {completion.model_service_provider} does not have an API key configured")

        base_url = provider.base_url if provider else None
        return MiroFishLLMClient(
            api_key=api_key,
            base_url=base_url,
            model=completion.model,
        )

    def _finalize_success(self, collection_id: str, target_revision: int, active_graph_id: str) -> bool:
        for session in get_sync_session():
            collection = session.get(db_models.Collection, collection_id)
            if not collection or collection.status == db_models.CollectionStatus.DELETED:
                return False

            config = parseCollectionConfig(collection.config)
            current_revision = config.graph_revision or 0
            if target_revision < current_revision:
                return False

            config.graph_status = GRAPH_STATUS_READY
            config.graph_status_message = build_graph_status_message(
                GRAPH_STATUS_READY,
                has_active_graph=True,
            )
            config.graph_error = None
            config.active_graph_id = active_graph_id
            config.active_graph_revision = target_revision
            config.graph_last_synced_at = utc_now()
            collection.config = dumpCollectionConfig(config)
            session.add(collection)
            session.commit()
            return True

    def _finalize_failure(self, collection_id: str, target_revision: int, error: str) -> bool:
        for session in get_sync_session():
            collection = session.get(db_models.Collection, collection_id)
            if not collection or collection.status == db_models.CollectionStatus.DELETED:
                return False

            config = parseCollectionConfig(collection.config)
            current_revision = config.graph_revision or 0
            if target_revision < current_revision:
                return False

            has_active_graph = bool(config.active_graph_id)
            config.graph_status = GRAPH_STATUS_FAILED
            config.graph_status_message = build_graph_status_message(
                GRAPH_STATUS_FAILED,
                has_active_graph=has_active_graph,
            )
            config.graph_error = error
            collection.config = dumpCollectionConfig(config)
            session.add(collection)
            session.commit()
            return True

    @staticmethod
    def _entity_type_from_node(node: dict) -> str:
        labels = list(node.get("labels") or [])
        for label in labels:
            if label not in {"Entity", "Node"}:
                return label
        return ""

    def _map_graph_node(self, node: dict) -> dict:
        entity_type = self._entity_type_from_node(node)
        chunk_ids = list(node.get("chunk_ids") or [])
        properties = {
            "entity_id": node["uuid"],
            "entity_name": node.get("name", ""),
            "entity_type": entity_type,
            "description": node.get("summary", ""),
            "aliases": node.get("aliases", []),
            "chunk_ids": chunk_ids,
            "created_at": node.get("created_at"),
        }
        for key, value in (node.get("attributes") or {}).items():
            properties[key] = value
        return {
            "id": node["uuid"],
            "labels": node.get("labels") or ([entity_type] if entity_type else []),
            "properties": properties,
        }

    def _map_graph_edge(self, edge: dict) -> dict:
        chunk_ids = [edge["source_chunk_id"]] if edge.get("source_chunk_id") else []
        return {
            "id": edge["uuid"],
            "type": edge.get("fact_type") or edge.get("name") or "DIRECTED",
            "source": edge["source_node_uuid"],
            "target": edge["target_node_uuid"],
            "properties": {
                "description": edge.get("fact", ""),
                "evidence": edge.get("evidence", ""),
                "confidence": edge.get("confidence", 0.5),
                "chunk_ids": chunk_ids,
                "source_chunk_id": edge.get("source_chunk_id"),
                "created_at": edge.get("created_at"),
                **(edge.get("attributes") or {}),
            },
        }


mirofish_graph_service = MiroFishGraphService()
