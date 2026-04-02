from __future__ import annotations

import hashlib
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

from aperag.config import settings

from .graph_extractor import ChunkGraphExtractor
from .graph_identity import (
    canonical_json,
    chunk_key,
    choose_preferred_name,
    collect_entity_aliases,
    document_key,
    entity_key,
    graph_key,
    normalize_name,
    prefer_entity_name,
    relation_key,
)
from .neo4j_client import Neo4jClientManager
from .neo4j_queries import (
    BATCH_UPSERT_CHUNKS_QUERY,
    BATCH_UPSERT_ENTITIES_QUERY,
    BATCH_UPSERT_RELATIONS_QUERY,
    BULK_LOAD_ENTITIES_QUERY,
    DELETE_GRAPH_QUERY,
    FIND_ENTITY_BY_ALIASES_QUERY,
    GRAPH_CHUNKS_QUERY,
    GRAPH_COUNTS_QUERY,
    GRAPH_DOCUMENTS_QUERY,
    GRAPH_METADATA_QUERY,
    GRAPH_NODES_QUERY,
    GRAPH_RELATIONS_QUERY,
    UPSERT_CHUNK_QUERY,
    UPSERT_DOCUMENT_QUERY,
    UPSERT_ENTITY_QUERY,
    UPSERT_GRAPH_QUERY,
    UPSERT_RELATION_QUERY,
)
from .text_processor import TextProcessor

logger = logging.getLogger(__name__)


class Neo4jGraphBackend:
    backend_name = "neo4j"

    def __init__(self, extractor: ChunkGraphExtractor | None = None) -> None:
        self.extractor = extractor

    def ensure_ready(self) -> None:
        Neo4jClientManager.ensure_ready()

    def build_graph(
        self,
        *,
        project: Any,
        text: str,
        ontology: dict[str, Any],
        graph_name: str,
        chunk_size: int,
        chunk_overlap: int,
        task_id: str,
    ) -> dict[str, Any]:
        self.ensure_ready()

        graph_id = graph_key(project.project_id)
        now = self._utcnow()
        documents = self._split_documents(project, text)
        parsed_documents, chunk_jobs = self._prepare_documents(
            project_id=project.project_id,
            documents=documents,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        with Neo4jClientManager.get_session() as session:
            session.run(DELETE_GRAPH_QUERY, graph_id=graph_id)
            session.run(
                UPSERT_GRAPH_QUERY,
                graph_id=graph_id,
                project_id=project.project_id,
                name=graph_name,
                description="MiroFish Neo4j graph",
                ontology_json=canonical_json(ontology),
                now=now,
            )
            self._upsert_documents(
                writer=session,
                graph_id=graph_id,
                project_id=project.project_id,
                parsed_documents=parsed_documents,
                now=now,
            )

        total_chunks = len(chunk_jobs)
        if total_chunks == 0:
            counts = self.get_graph_counts(graph_id)
            counts["chunk_count"] = 0
            return counts

        extracted_chunk_jobs = self._extract_chunk_jobs(chunk_jobs=chunk_jobs, ontology=ontology)

        entity_cache = self._bulk_load_entity_cache(graph_id)
        self._persist_chunks_batched(
            graph_id=graph_id,
            project_id=project.project_id,
            extracted_chunk_jobs=extracted_chunk_jobs,
            entity_cache=entity_cache,
        )

        counts = self.get_graph_counts(graph_id)
        counts["chunk_count"] = total_chunks
        return counts

    def append_documents(
        self,
        *,
        graph_id: str,
        project: Any,
        documents: list[dict[str, str]],
        ontology: dict[str, Any],
        graph_name: str,
        chunk_size: int,
        chunk_overlap: int,
        task_id: str,  # noqa: ARG002
    ) -> dict[str, Any]:
        self.ensure_ready()

        parsed_documents, chunk_jobs = self._prepare_documents(
            project_id=project.project_id,
            documents=documents,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        total_chunks = len(chunk_jobs)
        if total_chunks == 0:
            counts = self.get_graph_counts(graph_id)
            counts["chunk_count"] = 0
            counts["document_count"] = len(parsed_documents)
            return counts

        extracted_chunk_jobs = self._extract_chunk_jobs(chunk_jobs=chunk_jobs, ontology=ontology)
        now = self._utcnow()

        entity_cache = self._bulk_load_entity_cache(graph_id)

        with Neo4jClientManager.get_session() as session:
            tx = session.begin_transaction()
            try:
                tx.run(
                    UPSERT_GRAPH_QUERY,
                    graph_id=graph_id,
                    project_id=project.project_id,
                    name=graph_name,
                    description="MiroFish Neo4j graph",
                    ontology_json=canonical_json(ontology),
                    now=now,
                )
                self._upsert_documents(
                    writer=tx,
                    graph_id=graph_id,
                    project_id=project.project_id,
                    parsed_documents=parsed_documents,
                    now=now,
                )
                self._persist_chunks_batched(
                    graph_id=graph_id,
                    project_id=project.project_id,
                    extracted_chunk_jobs=extracted_chunk_jobs,
                    entity_cache=entity_cache,
                    writer=tx,
                )
                tx.commit()
            except Exception:
                tx.rollback()
                raise

        counts = self.get_graph_counts(graph_id)
        counts["chunk_count"] = total_chunks
        counts["document_count"] = len(parsed_documents)
        return counts

    def _extract_and_persist_chunk(
        self,
        *,
        graph_id: str,
        project_id: str,
        document_id: str,
        document_name: str,
        chunk_index: int,
        chunk_text: str,
        ontology: dict[str, Any],
    ) -> None:
        extracted = self.extractor.extract(
            chunk_text=chunk_text,
            ontology=ontology,
            document_name=document_name,
            chunk_index=chunk_index,
        )
        self._persist_chunk(
            graph_id=graph_id,
            project_id=project_id,
            document_id=document_id,
            chunk_index=chunk_index,
            chunk_text=chunk_text,
            extracted=extracted,
        )

    def _prepare_documents(
        self,
        *,
        project_id: str,
        documents: list[dict[str, str]],
        chunk_size: int,
        chunk_overlap: int,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        parsed_documents: list[dict[str, Any]] = []
        chunk_jobs: list[dict[str, Any]] = []
        for document in documents:
            document_id = document_key(project_id, document["filename"])
            chunks = TextProcessor.split_text(
                document["content"],
                chunk_size=chunk_size,
                overlap=chunk_overlap,
            )
            parsed_documents.append(
                {
                    "document_id": document_id,
                    "filename": document["filename"],
                    "content": document["content"],
                }
            )
            chunk_jobs.extend(
                [
                    {
                        "document_id": document_id,
                        "document_name": document["filename"],
                        "chunk_index": chunk_index,
                        "chunk_text": chunk_text,
                    }
                    for chunk_index, chunk_text in enumerate(chunks)
                ]
            )
        return parsed_documents, chunk_jobs

    def _upsert_documents(
        self,
        *,
        writer: Any,
        graph_id: str,
        project_id: str,
        parsed_documents: list[dict[str, Any]],
        now: str,
    ) -> None:
        for document in parsed_documents:
            writer.run(
                UPSERT_DOCUMENT_QUERY,
                graph_id=graph_id,
                project_id=project_id,
                id=document["document_id"],
                filename=document["filename"],
                display_name=document["filename"],
                content_checksum=self._checksum(document["content"]),
                now=now,
            )

    def _extract_chunk_jobs(
        self,
        *,
        chunk_jobs: list[dict[str, Any]],
        ontology: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if self.extractor is None:
            raise ValueError("Neo4jGraphBackend extractor is required for graph extraction")
        total_chunks = len(chunk_jobs)
        if total_chunks == 0:
            return []

        max_workers = max(1, min(settings.mirofish_graph_extraction_concurrency, total_chunks))
        extracted_jobs: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="mirofish-graph") as executor:
            futures = [
                executor.submit(
                    self.extractor.extract,
                    chunk_text=job["chunk_text"],
                    ontology=ontology,
                    document_name=job["document_name"],
                    chunk_index=job["chunk_index"],
                )
                for job in chunk_jobs
            ]
            for job, future in zip(chunk_jobs, futures, strict=False):
                extracted_jobs.append({**job, "extracted": future.result()})
        return extracted_jobs

    def get_graph_metadata(self, graph_id: str) -> dict[str, Any] | None:
        self.ensure_ready()
        with Neo4jClientManager.get_session() as session:
            record = session.run(GRAPH_METADATA_QUERY, graph_id=graph_id).single()
        if not record:
            return None
        return {
            "graph_id": record["graph_id"],
            "project_id": record["project_id"],
            "name": record["name"],
            "description": record["description"],
            "ontology": self._load_json(record.get("ontology_json")),
        }

    def get_graph_documents(self, graph_id: str) -> list[dict[str, Any]]:
        self.ensure_ready()
        documents: list[dict[str, Any]] = []
        with Neo4jClientManager.get_session() as session:
            records = session.run(GRAPH_DOCUMENTS_QUERY, graph_id=graph_id)
            for record in records:
                documents.append(
                    {
                        "id": record["id"],
                        "filename": record["filename"],
                        "display_name": record["display_name"],
                        "content_checksum": record["content_checksum"],
                        "updated_at": record["updated_at"],
                    }
                )
        return documents

    def get_graph_data(self, graph_id: str) -> dict[str, Any]:
        self.ensure_ready()
        nodes: list[dict[str, Any]] = []
        edges: list[dict[str, Any]] = []

        with Neo4jClientManager.get_session() as session:
            node_records = session.run(GRAPH_NODES_QUERY, graph_id=graph_id)
            for record in node_records:
                node = record["e"]
                chunk_ids = list(record.get("chunk_ids") or [])
                attributes = self._load_json(node.get("attributes_json"))
                entity_type = node.get("entity_type") or "Entity"
                nodes.append(
                    {
                        "uuid": node["id"],
                        "name": node.get("name", ""),
                        "aliases": list(node.get("aliases") or []),
                        "labels": ["Entity", entity_type],
                        "summary": node.get("summary", ""),
                        "attributes": attributes,
                        "chunk_ids": chunk_ids,
                        "created_at": str(node.get("created_at", "")),
                    }
                )

            relation_records = session.run(GRAPH_RELATIONS_QUERY, graph_id=graph_id)
            for record in relation_records:
                source = record["source"]
                target = record["target"]
                relation = record["r"]
                edges.append(
                    {
                        "uuid": relation["id"],
                        "name": relation.get("name", relation.get("fact_type", "RELATED_TO")),
                        "fact_type": relation.get("fact_type", relation.get("name", "RELATED_TO")),
                        "fact": relation.get("fact", ""),
                        "evidence": relation.get("evidence", ""),
                        "confidence": relation.get("confidence", 0.5),
                        "source_node_uuid": source["id"],
                        "target_node_uuid": target["id"],
                        "source_chunk_id": relation.get("source_chunk_id"),
                        "attributes": self._load_json(relation.get("attributes_json")),
                        "created_at": str(relation.get("created_at", "")),
                    }
                )

            chunk_records = session.run(GRAPH_CHUNKS_QUERY, graph_id=graph_id)
            chunks = []
            for record in chunk_records:
                document = record["d"]
                chunk = record["c"]
                chunks.append(
                    {
                        "id": chunk["id"],
                        "document_id": chunk.get("document_id"),
                        "document_display_name": document.get("display_name") or document.get("filename") or "",
                        "chunk_index": chunk.get("chunk_index"),
                        "content": chunk.get("content", ""),
                    }
                )

        return {
            "graph_id": graph_id,
            "nodes": nodes,
            "edges": edges,
            "chunks": chunks,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    def delete_graph(self, graph_id: str) -> None:
        self.ensure_ready()
        with Neo4jClientManager.get_session() as session:
            session.run(DELETE_GRAPH_QUERY, graph_id=graph_id)

    def get_graph_counts(self, graph_id: str) -> dict[str, Any]:
        """Return only node/edge/chunk counts without loading full graph data."""
        with Neo4jClientManager.get_session() as session:
            record = session.run(GRAPH_COUNTS_QUERY, graph_id=graph_id).single()
        if not record:
            return {"graph_id": graph_id, "node_count": 0, "edge_count": 0, "chunk_count": 0}
        return {
            "graph_id": graph_id,
            "node_count": record["node_count"],
            "edge_count": record["edge_count"],
            "chunk_count": record["chunk_count"],
        }

    def _bulk_load_entity_cache(self, graph_id: str) -> dict[tuple[str, str], dict[str, Any]]:
        """Pre-load all entities for a graph into an in-memory cache.

        Returns a dict keyed by (entity_type, normalized_name) -> {id, name, aliases}.
        Also indexes by all normalized_aliases for alias-based lookups.
        """
        cache: dict[tuple[str, str], dict[str, Any]] = {}
        with Neo4jClientManager.get_session() as session:
            records = session.run(BULK_LOAD_ENTITIES_QUERY, graph_id=graph_id)
            for record in records:
                entity_data = {
                    "id": record["id"],
                    "name": record["name"],
                    "aliases": list(record["aliases"] or []),
                }
                entity_type = record["entity_type"]
                # Index by normalized_name
                cache[(entity_type, record["normalized_name"])] = entity_data
                # Index by all normalized_aliases
                for alias in record["normalized_aliases"]:
                    if alias:
                        cache[(entity_type, alias)] = entity_data
        return cache

    def _find_entity_in_cache(
        self,
        *,
        entity_cache: dict[tuple[str, str], dict[str, Any]],
        entity_type: str,
        aliases: list[str],
    ) -> dict[str, Any] | None:
        """Look up an entity in the in-memory cache by any of its aliases."""
        for alias in aliases:
            norm = normalize_name(alias)
            if norm:
                hit = entity_cache.get((entity_type, norm))
                if hit:
                    return hit
        return None

    def _persist_chunks_batched(
        self,
        *,
        graph_id: str,
        project_id: str,
        extracted_chunk_jobs: list[dict[str, Any]],
        entity_cache: dict[tuple[str, str], dict[str, Any]],
        writer: Any | None = None,
    ) -> None:
        """Persist all extracted chunks using batched writes and an entity cache.

        This replaces the old sequential _persist_chunk() loop with:
        1. In-memory entity deduplication using entity_cache (no Neo4j lookups)
        2. Batched UNWIND queries for chunks, entities, and relations
        """
        if not extracted_chunk_jobs:
            return

        needs_session = writer is None
        if needs_session:
            session_ctx = Neo4jClientManager.get_session()
            writer = session_ctx.__enter__()
        else:
            session_ctx = None

        try:
            now = self._utcnow()

            chunk_batch: list[dict[str, Any]] = []
            entity_batch: list[dict[str, Any]] = []
            relation_batch: list[dict[str, Any]] = []
            # Track entity_id -> chunk_ids for the MENTIONS relationship via entity upsert
            entity_lookup: dict[tuple[str, str], str] = {}

            for job in extracted_chunk_jobs:
                chunk_id = chunk_key(project_id, job["document_id"], job["chunk_index"], job["chunk_text"])
                normalized = self._normalize_extracted_graph(job["extracted"])

                chunk_batch.append({
                    "graph_id": graph_id,
                    "project_id": project_id,
                    "document_id": job["document_id"],
                    "id": chunk_id,
                    "chunk_index": job["chunk_index"],
                    "content": job["chunk_text"],
                    "content_checksum": self._checksum(job["chunk_text"]),
                    "now": now,
                })

                # Process entities — use cache to resolve existing, skip Neo4j lookups
                chunk_entity_lookup: dict[tuple[str, str], str] = {}
                for entity in normalized.get("entities", []):
                    aliases = collect_entity_aliases(entity["name"], entity.get("aliases"))
                    existing = self._find_entity_in_cache(
                        entity_cache=entity_cache,
                        entity_type=entity["type"],
                        aliases=aliases,
                    )
                    existing_aliases = existing.get("aliases", []) if existing else []
                    final_name = choose_preferred_name(
                        entity["name"], existing.get("name") if existing else None, *aliases, *existing_aliases
                    )
                    final_aliases = collect_entity_aliases(final_name, [*aliases, *existing_aliases])
                    entity_id = existing.get("id") if existing else entity_key(graph_id, entity["type"], final_name)

                    # Update caches
                    normalized_aliases_list = [normalize_name(alias) for alias in final_aliases]
                    entity_data = {"id": entity_id, "name": final_name, "aliases": final_aliases}
                    for alias in final_aliases:
                        norm = normalize_name(alias)
                        if norm:
                            entity_cache[(entity["type"], norm)] = entity_data
                            chunk_entity_lookup[(entity["type"], norm)] = entity_id
                            entity_lookup[(entity["type"], norm)] = entity_id

                    entity_batch.append({
                        "graph_id": graph_id,
                        "project_id": project_id,
                        "chunk_id": chunk_id,
                        "id": entity_id,
                        "name": final_name,
                        "entity_type": entity["type"],
                        "normalized_name": normalize_name(final_name),
                        "aliases": final_aliases,
                        "normalized_aliases": normalized_aliases_list,
                        "summary": entity.get("summary", ""),
                        "attributes_json": canonical_json(entity.get("attributes")),
                        "now": now,
                    })

                # Process relations — use entity_lookup + entity_cache for endpoints
                for relation in normalized.get("relations", []):
                    source_id = self._resolve_relation_entity(
                        graph_id=graph_id,
                        project_id=project_id,
                        chunk_id=chunk_id,
                        entity_cache=entity_cache,
                        entity_lookup={**entity_lookup, **chunk_entity_lookup},
                        entity_batch=entity_batch,
                        entity_name=relation["source_name"],
                        entity_type=relation["source_type"],
                        now=now,
                    )
                    target_id = self._resolve_relation_entity(
                        graph_id=graph_id,
                        project_id=project_id,
                        chunk_id=chunk_id,
                        entity_cache=entity_cache,
                        entity_lookup={**entity_lookup, **chunk_entity_lookup},
                        entity_batch=entity_batch,
                        entity_name=relation["target_name"],
                        entity_type=relation["target_type"],
                        now=now,
                    )
                    rel_id = relation_key(
                        graph_id,
                        source_id,
                        relation["type"],
                        target_id,
                        relation.get("fact", ""),
                    )
                    relation_batch.append({
                        "graph_id": graph_id,
                        "project_id": project_id,
                        "id": rel_id,
                        "source_id": source_id,
                        "target_id": target_id,
                        "name": relation["type"],
                        "fact_type": relation["type"],
                        "fact": relation.get("fact", ""),
                        "evidence": relation.get("evidence", ""),
                        "confidence": relation.get("confidence", 0.5),
                        "attributes_json": canonical_json(relation.get("attributes")),
                        "source_chunk_id": chunk_id,
                        "now": now,
                    })

            # Execute batched writes: chunks first, then entities, then relations
            if chunk_batch:
                writer.run(BATCH_UPSERT_CHUNKS_QUERY, batch=chunk_batch)
            if entity_batch:
                writer.run(BATCH_UPSERT_ENTITIES_QUERY, batch=entity_batch)
            if relation_batch:
                writer.run(BATCH_UPSERT_RELATIONS_QUERY, batch=relation_batch)

        finally:
            if session_ctx is not None:
                session_ctx.__exit__(None, None, None)

    def _resolve_relation_entity(
        self,
        *,
        graph_id: str,
        project_id: str,
        chunk_id: str,
        entity_cache: dict[tuple[str, str], dict[str, Any]],
        entity_lookup: dict[tuple[str, str], str],
        entity_batch: list[dict[str, Any]],
        entity_name: str,
        entity_type: str,
        now: str,
    ) -> str:
        """Resolve a relation endpoint entity using in-memory lookups only.

        If the entity exists in entity_lookup or entity_cache, return its id.
        Otherwise create it in the entity_batch (no Neo4j round-trip).
        """
        aliases = collect_entity_aliases(entity_name)
        # Check entity_lookup first (covers entities from current build)
        for alias in aliases:
            key = (entity_type, normalize_name(alias))
            entity_id = entity_lookup.get(key)
            if entity_id:
                return entity_id

        # Check entity_cache (covers pre-existing entities)
        existing = self._find_entity_in_cache(
            entity_cache=entity_cache,
            entity_type=entity_type,
            aliases=aliases,
        )
        existing_aliases = existing.get("aliases", []) if existing else []
        final_name = choose_preferred_name(
            entity_name, existing.get("name") if existing else None, *aliases, *existing_aliases
        )
        final_aliases = collect_entity_aliases(final_name, [*aliases, *existing_aliases])
        entity_id = existing.get("id") if existing else entity_key(graph_id, entity_type, final_name)
        normalized_aliases_list = [normalize_name(alias) for alias in final_aliases]

        # Update caches
        entity_data = {"id": entity_id, "name": final_name, "aliases": final_aliases}
        for alias in final_aliases:
            norm = normalize_name(alias)
            if norm:
                entity_cache[(entity_type, norm)] = entity_data
                entity_lookup[(entity_type, norm)] = entity_id

        # Add to batch
        entity_batch.append({
            "graph_id": graph_id,
            "project_id": project_id,
            "chunk_id": chunk_id,
            "id": entity_id,
            "name": final_name,
            "entity_type": entity_type,
            "normalized_name": normalize_name(final_name),
            "aliases": final_aliases,
            "normalized_aliases": normalized_aliases_list,
            "summary": "",
            "attributes_json": "{}",
            "now": now,
        })
        return entity_id

    def _persist_chunk(
        self,
        *,
        graph_id: str,
        project_id: str,
        document_id: str,
        chunk_index: int,
        chunk_text: str,
        extracted: dict[str, Any],
        writer: Any | None = None,
    ) -> None:
        now = self._utcnow()
        chunk_id = chunk_key(project_id, document_id, chunk_index, chunk_text)
        normalized = self._normalize_extracted_graph(extracted)

        if writer is None:
            with Neo4jClientManager.get_session() as session:
                self._persist_chunk(
                    graph_id=graph_id,
                    project_id=project_id,
                    document_id=document_id,
                    chunk_index=chunk_index,
                    chunk_text=chunk_text,
                    extracted=extracted,
                    writer=session,
                )
            return

        writer.run(
            UPSERT_CHUNK_QUERY,
            graph_id=graph_id,
            project_id=project_id,
            document_id=document_id,
            id=chunk_id,
            chunk_index=chunk_index,
            content=chunk_text,
            content_checksum=self._checksum(chunk_text),
            now=now,
        )

        entity_lookup: dict[tuple[str, str], str] = {}
        for entity in normalized.get("entities", []):
            aliases = collect_entity_aliases(entity["name"], entity.get("aliases"))
            existing = self._find_existing_entity(
                session=writer,
                graph_id=graph_id,
                entity_type=entity["type"],
                aliases=aliases,
            )
            existing_aliases = existing.get("aliases", []) if existing else []
            final_name = choose_preferred_name(
                entity["name"], existing.get("name") if existing else None, *aliases, *existing_aliases
            )
            final_aliases = collect_entity_aliases(final_name, [*aliases, *existing_aliases])
            entity_id = existing.get("id") if existing else entity_key(graph_id, entity["type"], final_name)
            for alias in final_aliases:
                entity_lookup[(entity["type"], normalize_name(alias))] = entity_id
            writer.run(
                UPSERT_ENTITY_QUERY,
                graph_id=graph_id,
                project_id=project_id,
                chunk_id=chunk_id,
                id=entity_id,
                name=final_name,
                entity_type=entity["type"],
                normalized_name=normalize_name(final_name),
                aliases=final_aliases,
                normalized_aliases=[normalize_name(alias) for alias in final_aliases],
                summary=entity.get("summary", ""),
                attributes_json=canonical_json(entity.get("attributes")),
                now=now,
            )

        for relation in normalized.get("relations", []):
            source_id = self._ensure_relation_entity(
                session=writer,
                graph_id=graph_id,
                project_id=project_id,
                chunk_id=chunk_id,
                entity_lookup=entity_lookup,
                entity_name=relation["source_name"],
                entity_type=relation["source_type"],
                now=now,
            )
            target_id = self._ensure_relation_entity(
                session=writer,
                graph_id=graph_id,
                project_id=project_id,
                chunk_id=chunk_id,
                entity_lookup=entity_lookup,
                entity_name=relation["target_name"],
                entity_type=relation["target_type"],
                now=now,
            )
            relation_id = relation_key(
                graph_id,
                source_id,
                relation["type"],
                target_id,
                relation.get("fact", ""),
            )
            writer.run(
                UPSERT_RELATION_QUERY,
                graph_id=graph_id,
                project_id=project_id,
                id=relation_id,
                source_id=source_id,
                target_id=target_id,
                name=relation["type"],
                fact_type=relation["type"],
                fact=relation.get("fact", ""),
                evidence=relation.get("evidence", ""),
                confidence=relation.get("confidence", 0.5),
                attributes_json=canonical_json(relation.get("attributes")),
                source_chunk_id=chunk_id,
                now=now,
            )

    def _ensure_relation_entity(
        self,
        *,
        session: Any,
        graph_id: str,
        project_id: str,
        chunk_id: str,
        entity_lookup: dict[tuple[str, str], str],
        entity_name: str,
        entity_type: str,
        now: str,
    ) -> str:
        aliases = collect_entity_aliases(entity_name)
        for alias in aliases:
            key = (entity_type, normalize_name(alias))
            entity_id = entity_lookup.get(key)
            if entity_id:
                return entity_id

        existing = self._find_existing_entity(
            session=session,
            graph_id=graph_id,
            entity_type=entity_type,
            aliases=aliases,
        )
        existing_aliases = existing.get("aliases", []) if existing else []
        final_name = choose_preferred_name(
            entity_name, existing.get("name") if existing else None, *aliases, *existing_aliases
        )
        final_aliases = collect_entity_aliases(final_name, [*aliases, *existing_aliases])
        entity_id = existing.get("id") if existing else entity_key(graph_id, entity_type, final_name)
        for alias in final_aliases:
            entity_lookup[(entity_type, normalize_name(alias))] = entity_id
        session.run(
            UPSERT_ENTITY_QUERY,
            graph_id=graph_id,
            project_id=project_id,
            chunk_id=chunk_id,
            id=entity_id,
            name=final_name,
            entity_type=entity_type,
            normalized_name=normalize_name(final_name),
            aliases=final_aliases,
            normalized_aliases=[normalize_name(alias) for alias in final_aliases],
            summary="",
            attributes_json="{}",
            now=now,
        )
        return entity_id

    def _normalize_extracted_graph(self, extracted: dict[str, Any]) -> dict[str, Any]:
        grouped_entities: dict[tuple[str, str], dict[str, Any]] = {}
        alias_map: dict[tuple[str, str], tuple[str, str]] = {}

        for entity in extracted.get("entities", []):
            entity_type = entity["type"]
            attributes = entity.get("attributes") or {}
            alias_inputs = [entity.get("aliases"), attributes]
            preferred_name = prefer_entity_name(entity["name"], alias_inputs)
            aliases = collect_entity_aliases(entity["name"], alias_inputs)
            key = (entity_type, normalize_name(preferred_name))
            existing = grouped_entities.get(key)
            merged_aliases = aliases if not existing else [*existing.get("aliases", []), *aliases]
            merged_attributes = dict(existing.get("attributes", {})) if existing else {}
            merged_attributes.update({k: v for k, v in attributes.items() if v not in (None, "", [], {})})
            summary = (existing.get("summary", "") if existing else "") or entity.get("summary", "")
            grouped_entities[key] = {
                "name": choose_preferred_name(preferred_name, existing.get("name") if existing else None, *merged_aliases),
                "type": entity_type,
                "summary": summary,
                "attributes": merged_attributes,
                "aliases": collect_entity_aliases(preferred_name, [merged_aliases, merged_attributes]),
            }
            for alias in grouped_entities[key]["aliases"]:
                alias_map[(entity_type, normalize_name(alias))] = key

        relations: list[dict[str, Any]] = []
        for relation in extracted.get("relations", []):
            source_key = alias_map.get((relation["source_type"], normalize_name(relation["source_name"])))
            target_key = alias_map.get((relation["target_type"], normalize_name(relation["target_name"])))
            source_name = grouped_entities[source_key]["name"] if source_key else relation["source_name"]
            target_name = grouped_entities[target_key]["name"] if target_key else relation["target_name"]
            relations.append({**relation, "source_name": source_name, "target_name": target_name})

        return {
            "entities": list(grouped_entities.values()),
            "relations": relations,
        }

    def _find_existing_entity(
        self,
        *,
        session: Any,
        graph_id: str,
        entity_type: str,
        aliases: list[str],
    ) -> dict[str, Any] | None:
        normalized_aliases = [normalize_name(alias) for alias in aliases if normalize_name(alias)]
        if not normalized_aliases:
            return None

        record = session.run(
            FIND_ENTITY_BY_ALIASES_QUERY,
            graph_id=graph_id,
            entity_type=entity_type,
            normalized_aliases=normalized_aliases,
        ).single()
        if not record:
            return None

        return {
            "id": record["id"],
            "name": record["name"],
            "aliases": list(record["aliases"] or []),
        }

    def _split_documents(self, project: Any, text: str) -> list[dict[str, str]]:
        sections = []
        pattern = re.compile(r"(?:^|\n\n)=== (?P<filename>.+?) ===\n", re.MULTILINE)
        matches = list(pattern.finditer(text))
        if matches:
            for index, match in enumerate(matches):
                start = match.end()
                end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
                content = text[start:end].strip()
                if content:
                    sections.append({"filename": match.group("filename").strip(), "content": content})
        if not sections:
            fallback_name = getattr(project, "name", None) or "document.txt"
            sections.append({"filename": fallback_name, "content": text})
        return sections

    @staticmethod
    def _checksum(value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _load_json(value: Any) -> dict[str, Any]:
        if not value:
            return {}
        if isinstance(value, dict):
            return value
        try:
            return json.loads(value)
        except Exception:
            return {}

    @staticmethod
    def _utcnow() -> str:
        return datetime.now(timezone.utc).isoformat()
