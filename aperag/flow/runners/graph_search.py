# Copyright 2025 ApeCloud, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import re
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from aperag.db.models import Collection
from aperag.db.ops import async_db_ops
from aperag.flow.base.models import BaseNodeRunner, SystemInput, register_node_runner
from aperag.mirofish_graph.helpers import is_mirofish_collection_config
from aperag.query.query import DocumentWithScore
from aperag.schema.utils import parseCollectionConfig

logger = logging.getLogger(__name__)


# User input model for graph search node
class GraphSearchInput(BaseModel):
    top_k: int = Field(12, description="Number of top results to return")
    collection_ids: Optional[list[str]] = Field(default_factory=list, description="Collection IDs")


# User output model for graph search node
class GraphSearchOutput(BaseModel):
    docs: List[DocumentWithScore]


# Database operations interface
class GraphSearchRepository:
    """Repository interface for graph search database operations"""

    async def get_collection(self, user, collection_id: str) -> Optional[Collection]:
        """Get collection by ID for the user"""
        return await async_db_ops.query_collection(user, collection_id)


# Business logic service
class GraphSearchService:
    """Service class containing graph search business logic"""

    def __init__(self, repository: GraphSearchRepository):
        self.repository = repository

    @staticmethod
    def _extract_query_terms(query: str) -> list[str]:
        raw_terms = re.findall(r"[\u4e00-\u9fff]{1,}|[A-Za-z0-9_]{2,}", (query or "").lower())
        terms: list[str] = []
        seen: set[str] = set()
        for term in raw_terms:
            cleaned = term.strip()
            if len(cleaned) < 2 and not re.search(r"[\u4e00-\u9fff]", cleaned):
                continue
            if cleaned in seen:
                continue
            seen.add(cleaned)
            terms.append(cleaned)
        if query and query.lower() not in seen:
            terms.append(query.lower())
        return terms

    @staticmethod
    def _score_text(text: str, terms: list[str]) -> float:
        normalized = (text or "").lower()
        if not normalized:
            return 0.0
        score = 0.0
        for term in terms:
            if not term:
                continue
            occurrences = normalized.count(term)
            if not occurrences:
                continue
            score += occurrences * max(len(term), 1)
        return score

    @staticmethod
    def _format_mirofish_graph_context(
        *,
        entities: list[dict],
        relationships: list[dict],
        chunks: list[dict],
    ) -> str:
        return "\n".join(
            [
                f"Entities(KG): {entities}",
                f"Relationships(KG): {relationships}",
                f"Document Chunks(DC): {chunks}",
            ]
        )

    async def _execute_mirofish_graph_search(self, user: str, collection_id: str, query: str, top_k: int):
        from aperag.service.mirofish_graph_service import mirofish_graph_service

        graph_snapshot = await mirofish_graph_service.get_graph_snapshot(user, collection_id)
        nodes = list(graph_snapshot.get("nodes") or [])
        edges = list(graph_snapshot.get("edges") or [])
        chunks = list(graph_snapshot.get("chunks") or [])
        if not nodes or not edges:
            logger.warning("Collection %s uses MiroFish graph engine but has no graph snapshot data", collection_id)
            return []

        terms = self._extract_query_terms(query)
        ranked_chunks = []
        for chunk in chunks:
            content = str(chunk.get("content") or "")
            document_name = str(chunk.get("document_display_name") or "")
            score = self._score_text(f"{document_name}\n{content}", terms)
            if score > 0:
                ranked_chunks.append((score, chunk))

        ranked_chunks.sort(key=lambda item: item[0], reverse=True)
        selected_chunks = [item[1] for item in ranked_chunks[: max(top_k * 2, 4)]]
        if not selected_chunks:
            selected_chunks = chunks[: max(top_k, 3)]

        selected_chunk_ids = {
            str(chunk.get("id") or "").strip()
            for chunk in selected_chunks
            if str(chunk.get("id") or "").strip()
        }
        selected_edges = []
        selected_node_ids: set[str] = set()
        for edge in edges:
            source_chunk_id = str(edge.get("source_chunk_id") or "").strip()
            haystack = "\n".join(
                [
                    str(edge.get("fact_type") or ""),
                    str(edge.get("fact") or ""),
                    str(edge.get("evidence") or ""),
                ]
            )
            if source_chunk_id in selected_chunk_ids or self._score_text(haystack, terms) > 0:
                selected_edges.append(edge)
                if edge.get("source_node_uuid"):
                    selected_node_ids.add(str(edge["source_node_uuid"]))
                if edge.get("target_node_uuid"):
                    selected_node_ids.add(str(edge["target_node_uuid"]))

        for node in nodes:
            node_chunk_ids = {
                str(chunk_id).strip()
                for chunk_id in (node.get("chunk_ids") or [])
                if str(chunk_id).strip()
            }
            haystack = "\n".join(
                [
                    str(node.get("name") or ""),
                    str(node.get("summary") or ""),
                    " ".join(str(label) for label in (node.get("labels") or [])),
                ]
            )
            if node_chunk_ids & selected_chunk_ids or self._score_text(haystack, terms) > 0:
                selected_node_ids.add(str(node.get("uuid") or ""))

        if not selected_node_ids and not selected_edges:
            selected_edges = edges[:top_k]
            for edge in selected_edges:
                if edge.get("source_node_uuid"):
                    selected_node_ids.add(str(edge["source_node_uuid"]))
                if edge.get("target_node_uuid"):
                    selected_node_ids.add(str(edge["target_node_uuid"]))

        selected_nodes = [node for node in nodes if str(node.get("uuid") or "") in selected_node_ids][: max(top_k * 2, 6)]
        selected_edges = selected_edges[: max(top_k * 2, 6)]
        selected_chunk_ids = {
            str(edge.get("source_chunk_id") or "").strip()
            for edge in selected_edges
            if str(edge.get("source_chunk_id") or "").strip()
        } | {
            str(chunk_id).strip()
            for node in selected_nodes
            for chunk_id in (node.get("chunk_ids") or [])
            if str(chunk_id).strip()
        }
        selected_chunks = [chunk for chunk in chunks if str(chunk.get("id") or "").strip() in selected_chunk_ids][: max(top_k * 2, 6)]

        entities_payload = [
            {
                "id": str(node.get("uuid") or ""),
                "entity": str(node.get("name") or ""),
                "type": str((node.get("labels") or ["Entity"])[-1] or "Entity"),
                "description": str(node.get("summary") or ""),
                "rank": index + 1,
            }
            for index, node in enumerate(selected_nodes)
        ]
        relationships_payload = [
            {
                "id": str(edge.get("uuid") or ""),
                "entity1": str(edge.get("source_name") or edge.get("source_node_uuid") or ""),
                "entity2": str(edge.get("target_name") or edge.get("target_node_uuid") or ""),
                "description": str(edge.get("fact") or edge.get("evidence") or ""),
                "keywords": str(edge.get("fact_type") or ""),
                "weight": edge.get("confidence") or 1.0,
                "rank": index + 1,
            }
            for index, edge in enumerate(selected_edges)
        ]
        chunks_payload = [
            {
                "id": str(chunk.get("id") or ""),
                "document": str(chunk.get("document_display_name") or ""),
                "content": str(chunk.get("content") or "")[:600],
            }
            for chunk in selected_chunks
        ]
        if not entities_payload and not relationships_payload:
            return []

        context = self._format_mirofish_graph_context(
            entities=entities_payload,
            relationships=relationships_payload,
            chunks=chunks_payload,
        )
        return [DocumentWithScore(text=context, metadata={"recall_type": "graph_search"})]

    async def execute_graph_search(
        self, user, query: str, top_k: int, collection_ids: List[str]
    ) -> List[DocumentWithScore]:
        """Execute graph search with given parameters"""
        collection = None
        if collection_ids:
            collection = await self.repository.get_collection(user, collection_ids[0])

        if not collection:
            return []

        config = parseCollectionConfig(collection.config)
        if is_mirofish_collection_config(config):
            return await self._execute_mirofish_graph_search(user, collection.id, query, top_k)

        if not config.enable_knowledge_graph:
            logger.warning(f"Collection {collection.id} does not have knowledge graph enabled")
            return []

        # Import LightRAG and run as in _run_light_rag
        from aperag.graph import lightrag_manager
        from aperag.graph.lightrag import QueryParam

        rag = await lightrag_manager.create_lightrag_instance(collection)
        param: QueryParam = QueryParam(
            mode="hybrid",
            only_need_context=True,
            top_k=top_k,
        )
        context = await rag.aquery_context(query=query, param=param)
        if not context:
            return []

        # Return documents with graph search metadata
        return [DocumentWithScore(text=context, metadata={"recall_type": "graph_search"})]


@register_node_runner(
    "graph_search",
    input_model=GraphSearchInput,
    output_model=GraphSearchOutput,
)
class GraphSearchNodeRunner(BaseNodeRunner):
    def __init__(self):
        self.repository = GraphSearchRepository()
        self.service = GraphSearchService(self.repository)

    async def run(self, ui: GraphSearchInput, si: SystemInput) -> Tuple[GraphSearchOutput, dict]:
        """
        Run graph search node. ui: user configurable params; si: system injected params (SystemInput).
        Returns (uo, so)
        """
        docs = await self.service.execute_graph_search(
            user=si.user, query=si.query, top_k=ui.top_k, collection_ids=ui.collection_ids or []
        )

        return GraphSearchOutput(docs=docs), {}
