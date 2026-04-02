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
    GRAPH_STATUS_WAITING_FOR_DOCUMENTS,
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

        skip_result = self._skip_if_request_not_current(
            collection_id,
            target_revision,
            stage="preflight",
            collection=collection,
            config=config,
        )
        if skip_result:
            return skip_result

        llm_client = self._build_llm_client(collection, config)
        ontology_generator = OntologyGenerator(llm_client)
        backend = Neo4jGraphBackend(ChunkGraphExtractor(llm_client))

        documents = self._load_confirmed_documents(collection)
        if not documents:
            raise ValueError(f"No confirmed documents are available for collection {collection_id}")

        if config.active_graph_id:
            graph_metadata = backend.get_graph_metadata(config.active_graph_id)
            if not graph_metadata:
                raise ValueError(f"Active graph metadata is unavailable for collection {collection_id}")

            graph_documents = backend.get_graph_documents(config.active_graph_id)
            incremental_documents = self._select_incremental_documents(documents, graph_documents)
            if not incremental_documents:
                if not self._finalize_success(collection_id, target_revision, config.active_graph_id):
                    return {"collection_id": collection_id, "stale": True, "graph_id": config.active_graph_id}
                graph_data = backend.get_graph_data(config.active_graph_id)
                return {
                    "collection_id": collection_id,
                    "graph_id": config.active_graph_id,
                    "revision": target_revision,
                    "node_count": graph_data.get("node_count", 0),
                    "edge_count": graph_data.get("edge_count", 0),
                    "document_count": 0,
                    "chunk_count": 0,
                    "no_changes": True,
                    "incremental": True,
                }

            skip_result = self._skip_if_request_not_current(
                collection_id,
                target_revision,
                stage="before_incremental_payloads",
            )
            if skip_result:
                return skip_result

            document_payloads = self._collect_document_payloads(collection, incremental_documents)
            if not document_payloads:
                if not self._finalize_success(collection_id, target_revision, config.active_graph_id):
                    return {"collection_id": collection_id, "stale": True, "graph_id": config.active_graph_id}
                graph_data = backend.get_graph_data(config.active_graph_id)
                return {
                    "collection_id": collection_id,
                    "graph_id": config.active_graph_id,
                    "revision": target_revision,
                    "node_count": graph_data.get("node_count", 0),
                    "edge_count": graph_data.get("edge_count", 0),
                    "document_count": len(incremental_documents),
                    "chunk_count": 0,
                    "no_changes": True,
                    "incremental": True,
                }

            ontology = graph_metadata.get("ontology") or {}
            if not ontology:
                raise ValueError(f"Active graph ontology is unavailable for collection {collection_id}")

            skip_result = self._skip_if_request_not_current(
                collection_id,
                target_revision,
                stage="before_incremental_append",
            )
            if skip_result:
                return skip_result

            project = _MiroFishProject(
                project_id=graph_metadata.get("project_id") or f"{collection.id}:active",
                name=collection.title or collection.id,
            )
            graph_data = backend.append_documents(
                graph_id=config.active_graph_id,
                project=project,
                documents=document_payloads,
                ontology=ontology,
                graph_name=graph_metadata.get("name") or f"{collection.title or collection.id} active",
                chunk_size=settings.mirofish_graph_chunk_size,
                chunk_overlap=settings.mirofish_graph_chunk_overlap,
                task_id=f"{collection.id}:{target_revision}",
            )

            if not self._finalize_success(collection_id, target_revision, config.active_graph_id):
                return {"collection_id": collection_id, "stale": True, "graph_id": config.active_graph_id}

            return {
                "collection_id": collection_id,
                "graph_id": config.active_graph_id,
                "revision": target_revision,
                "node_count": graph_data.get("node_count", 0),
                "edge_count": graph_data.get("edge_count", 0),
                "document_count": graph_data.get("document_count", len(document_payloads)),
                "chunk_count": graph_data.get("chunk_count", 0),
                "incremental": True,
            }

        skip_result = self._skip_if_request_not_current(
            collection_id,
            target_revision,
            stage="before_initial_payloads",
        )
        if skip_result:
            return skip_result

        document_payloads = self._collect_document_payloads(collection, documents)
        document_sections, document_texts = self._payloads_to_sections_and_texts(document_payloads)
        if not document_sections:
            raise ValueError(f"No confirmed documents are available for collection {collection_id}")

        skip_result = self._skip_if_request_not_current(
            collection_id,
            target_revision,
            stage="before_initial_ontology",
        )
        if skip_result:
            return skip_result

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

        skip_result = self._skip_if_request_not_current(
            collection_id,
            target_revision,
            stage="before_initial_build",
        )
        if skip_result:
            return skip_result

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
            "document_count": len(document_payloads),
            "chunk_count": graph_data.get("chunk_count", 0),
            "incremental": False,
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

    def get_document_graph_statuses(
        self,
        collection: db_models.Collection,
        documents: list[db_models.Document],
    ) -> dict[str, str]:
        config = parseCollectionConfig(collection.config)
        if not is_mirofish_collection_config(config) or not documents:
            return {}

        active_graph_filenames: set[str] = set()
        if config.active_graph_id:
            try:
                active_graph_filenames = self._get_active_graph_document_names(config.active_graph_id)
            except Exception as exc:
                logger.warning(
                    "Failed to load active graph document snapshot for collection %s: %s",
                    collection.id,
                    exc,
                )

        graph_status = config.graph_status or GRAPH_STATUS_WAITING_FOR_DOCUMENTS
        return {
            document.id: self._derive_document_graph_status(
                document=document,
                graph_status=graph_status,
                active_graph_filenames=active_graph_filenames,
            )
            for document in documents
            if document.id
        }

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

    def _get_active_graph_document_names(self, active_graph_id: str) -> set[str]:
        backend = Neo4jGraphBackend()
        return {
            name
            for document in backend.get_graph_documents(active_graph_id)
            for name in [str(document.get("filename") or document.get("display_name") or "").strip()]
            if name
        }

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
        payloads = self._collect_document_payloads(collection, documents)
        return self._payloads_to_sections_and_texts(payloads)

    def _collect_document_payloads(
        self,
        collection: db_models.Collection,
        documents: list[db_models.Document],
    ) -> list[dict[str, str]]:
        payloads: list[dict[str, str]] = []
        for document in documents:
            cached_content = self._read_cached_document_markdown(document)
            if cached_content:
                payloads.append({"filename": document.name, "content": cached_content})
                continue

            local_doc = None
            try:
                content, _, local_doc = parse_document_content(document, collection)
                content = (content or "").strip()
                if not content:
                    continue
                payloads.append({"filename": document.name, "content": content})
            except Exception as exc:
                logger.warning(
                    "Failed to parse collection document %s for MiroFish graph build: %s",
                    document.id,
                    exc,
                )
            finally:
                if local_doc is not None:
                    cleanup_local_document(local_doc, collection)
        return payloads

    @staticmethod
    def _payloads_to_sections_and_texts(payloads: list[dict[str, str]]) -> tuple[list[str], list[str]]:
        sections: list[str] = []
        document_texts: list[str] = []
        for payload in payloads:
            content = (payload.get("content") or "").strip()
            filename = (payload.get("filename") or "").strip()
            if not content or not filename:
                continue
            sections.append(f"=== {filename} ===\n{content}")
            document_texts.append(content)
        return sections, document_texts

    @staticmethod
    def _select_incremental_documents(
        documents: list[db_models.Document],
        graph_documents: list[dict],
    ) -> list[db_models.Document]:
        existing_filenames = {
            str(doc.get("filename") or doc.get("display_name") or "").strip()
            for doc in graph_documents
            if str(doc.get("filename") or doc.get("display_name") or "").strip()
        }
        return [document for document in documents if (document.name or "").strip() not in existing_filenames]

    @staticmethod
    def _derive_document_graph_status(
        *,
        document: db_models.Document,
        graph_status: str,
        active_graph_filenames: set[str],
    ) -> str:
        document_name = (document.name or "").strip()
        if document_name and document_name in active_graph_filenames:
            return db_models.DocumentIndexStatus.ACTIVE.value

        if document.status == db_models.DocumentStatus.FAILED:
            return db_models.DocumentIndexStatus.FAILED.value

        if graph_status == GRAPH_STATUS_FAILED:
            return db_models.DocumentIndexStatus.FAILED.value

        if graph_status in {GRAPH_STATUS_BUILDING, GRAPH_STATUS_UPDATING}:
            return db_models.DocumentIndexStatus.CREATING.value

        return db_models.DocumentIndexStatus.PENDING.value

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
            raise ValueError(
                f"集合 {collection.id} 未配置有效的 completion model。\n"
                f"请检查集合配置中的模型设置。"
            )

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
            raise ValueError(
                f"LLM Provider '{completion.model_service_provider}' 未配置 API Key。\n\n"
                f"解决方案:\n"
                f"1. 在 UI 中进入 Settings > Models > API Keys 配置该 provider 的 API Key\n"
                f"2. 如果使用的是本地 Ollama，可以填写任意字符串（如 'ollama'）\n"
            )

        if not provider:
            raise ValueError(
                f"LLM Provider '{completion.model_service_provider}' 未找到。\n\n"
                f"解决方案:\n"
                f"1. 检查集合配置中的 model_service_provider 设置\n"
                f"2. 在 UI 中 Settings > Models 中确认该 provider 已添加\n"
            )

        base_url = provider.base_url
        if not base_url:
            raise ValueError(
                f"LLM Provider '{completion.model_service_provider}' 未配置 base_url。\n\n"
                f"请检查 provider 配置中的 base_url 设置。"
            )

        return MiroFishLLMClient(
            api_key=api_key,
            base_url=base_url,
            model=completion.model,
        )

    def _get_request_state(
        self,
        collection_id: str,
        target_revision: int,
        *,
        collection: db_models.Collection | None = None,
        config=None,
    ) -> tuple[str, db_models.Collection, object]:
        current_collection = collection or self.sync_db_ops.query_collection_by_id(collection_id)
        if not current_collection:
            raise CollectionNotFoundException(collection_id)

        current_config = config or parseCollectionConfig(current_collection.config)
        current_revision = current_config.graph_revision or 0
        active_revision = current_config.active_graph_revision or 0

        if target_revision < current_revision:
            return "stale", current_collection, current_config

        if current_config.active_graph_id and active_revision and target_revision <= active_revision:
            return "already_synchronized", current_collection, current_config

        return "current", current_collection, current_config

    def _build_skip_result(
        self,
        collection_id: str,
        target_revision: int,
        *,
        reason: str,
        config,
        stage: str,
    ) -> dict:
        result = {
            "collection_id": collection_id,
            "target_revision": target_revision,
            "current_revision": config.graph_revision or 0,
            "active_graph_revision": config.active_graph_revision,
            "graph_id": config.active_graph_id,
            "skipped": True,
            "reason": reason,
            "stage": stage,
        }
        if reason == "stale":
            result["stale"] = True
        if reason == "already_synchronized":
            result["already_synchronized"] = True
        return result

    def _skip_if_request_not_current(
        self,
        collection_id: str,
        target_revision: int,
        *,
        stage: str,
        collection: db_models.Collection | None = None,
        config=None,
    ) -> dict | None:
        request_state, _, current_config = self._get_request_state(
            collection_id,
            target_revision,
            collection=collection,
            config=config,
        )
        if request_state == "current":
            return None

        logger.info(
            "Skip MiroFish graph build for collection %s at stage %s: request revision %s is %s "
            "(current=%s, active=%s)",
            collection_id,
            stage,
            target_revision,
            request_state,
            current_config.graph_revision or 0,
            current_config.active_graph_revision,
        )
        return self._build_skip_result(
            collection_id,
            target_revision,
            reason=request_state,
            config=current_config,
            stage=stage,
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
