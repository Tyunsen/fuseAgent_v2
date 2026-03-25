from __future__ import annotations

import logging
import re
from typing import Iterable

from aperag.mirofish_graph.helpers import is_mirofish_collection_config
from aperag.schema import view_models

logger = logging.getLogger(__name__)


SOURCE_ID_SPLIT_PATTERN = re.compile(r"(?:<SEP>|\|)")


def _normalize_text(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _split_source_ids(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_split_source_ids(item))
        return result

    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in SOURCE_ID_SPLIT_PATTERN.split(text) if part.strip()]


def _dedupe_preserve_order(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


class AnswerGraphService:
    def __init__(self) -> None:
        from aperag.service.collection_service import collection_service
        from aperag.service.graph_service import graph_service
        from aperag.service.mirofish_graph_service import mirofish_graph_service

        self.collection_service = collection_service
        self.graph_service = graph_service
        self.mirofish_graph_service = mirofish_graph_service

    async def get_answer_graph(
        self,
        user_id: str,
        collection_id: str,
        request: view_models.AnswerGraphRequest,
    ) -> view_models.AnswerGraphResponse:
        collection = await self.collection_service.get_collection(user_id, collection_id)
        references = request.references or []
        if not references:
            return self._empty_response("no_references")

        if is_mirofish_collection_config(collection.config):
            return await self._get_mirofish_answer_graph(
                user_id=user_id,
                collection_id=collection_id,
                references=references,
                max_nodes=request.max_nodes or 24,
            )

        return await self._get_standard_answer_graph(
            user_id=user_id,
            collection_id=collection_id,
            references=references,
            max_nodes=request.max_nodes or 24,
        )

    async def _get_mirofish_answer_graph(
        self,
        *,
        user_id: str,
        collection_id: str,
        references: list[view_models.AnswerGraphReferenceInput],
        max_nodes: int,
    ) -> view_models.AnswerGraphResponse:
        graph_snapshot = await self.mirofish_graph_service.get_graph_snapshot(user_id, collection_id)
        chunks = list(graph_snapshot.get("chunks") or [])
        if not chunks:
            return self._empty_response("graph_unavailable")

        row_to_chunk_ids = self._match_mirofish_rows_to_chunks(references, chunks)
        all_chunk_ids = {
            chunk_id
            for chunk_ids in row_to_chunk_ids.values()
            for chunk_id in chunk_ids
            if chunk_id
        }
        if not all_chunk_ids:
            return self._empty_response("no_matching_graph_elements")

        selected_edges = []
        selected_node_ids: set[str] = set()
        for edge in graph_snapshot.get("edges", []):
            source_chunk_id = str(edge.get("source_chunk_id") or "").strip()
            if source_chunk_id and source_chunk_id in all_chunk_ids:
                selected_edges.append(edge)
                selected_node_ids.add(edge["source_node_uuid"])
                selected_node_ids.add(edge["target_node_uuid"])

        for node in graph_snapshot.get("nodes", []):
            node_chunk_ids = set(_split_source_ids(node.get("chunk_ids")))
            if node_chunk_ids & all_chunk_ids:
                selected_node_ids.add(node["uuid"])

        selected_nodes = [node for node in graph_snapshot.get("nodes", []) if node["uuid"] in selected_node_ids]
        if not selected_nodes and not selected_edges:
            return self._empty_response("no_matching_graph_elements")

        row_chunk_lookup = {row_id: set(chunk_ids) for row_id, chunk_ids in row_to_chunk_ids.items()}

        nodes = []
        for node in selected_nodes:
            mapped = self.mirofish_graph_service._map_graph_node(node)
            chunk_ids = _dedupe_preserve_order(_split_source_ids(node.get("chunk_ids")))
            linked_row_ids = self._resolve_linked_rows(row_chunk_lookup, chunk_ids)
            mapped["properties"]["chunk_ids"] = chunk_ids
            mapped["properties"]["linked_row_ids"] = linked_row_ids
            nodes.append(mapped)

        edges = []
        for edge in selected_edges:
            mapped = self.mirofish_graph_service._map_graph_edge(edge)
            chunk_ids = _dedupe_preserve_order(_split_source_ids(edge.get("source_chunk_id")))
            linked_row_ids = self._resolve_linked_rows(row_chunk_lookup, chunk_ids)
            mapped["properties"]["chunk_ids"] = chunk_ids
            mapped["properties"]["linked_row_ids"] = linked_row_ids
            edges.append(mapped)

        nodes = self._limit_nodes(nodes, edges, max_nodes)
        allowed_node_ids = {node["id"] for node in nodes}
        edges = [edge for edge in edges if edge["source"] in allowed_node_ids and edge["target"] in allowed_node_ids]
        linked_row_ids = sorted(
            {
                row_id
                for item in [*nodes, *edges]
                for row_id in item.get("properties", {}).get("linked_row_ids", [])
            }
        )
        return view_models.AnswerGraphResponse(
            nodes=nodes,
            edges=edges,
            linked_row_ids=linked_row_ids,
            is_empty=False,
            empty_reason=None,
        )

    async def _get_standard_answer_graph(
        self,
        *,
        user_id: str,
        collection_id: str,
        references: list[view_models.AnswerGraphReferenceInput],
        max_nodes: int,
    ) -> view_models.AnswerGraphResponse:
        row_chunk_lookup = {
            reference.source_row_id: set(_dedupe_preserve_order(reference.chunk_ids))
            for reference in references
            if reference.chunk_ids
        }
        all_chunk_ids = {chunk_id for chunk_ids in row_chunk_lookup.values() for chunk_id in chunk_ids}
        if not all_chunk_ids:
            return self._empty_response("graph_linking_unavailable")

        graph_window = min(max(max_nodes * 8, 200), 2000)
        graph = await self.graph_service.get_knowledge_graph(
            user_id=user_id,
            collection_id=collection_id,
            label="*",
            max_depth=3,
            max_nodes=graph_window,
        )

        nodes = []
        for node in graph.get("nodes", []):
            chunk_ids = self._extract_graph_chunk_ids(node.get("properties", {}))
            if set(chunk_ids) & all_chunk_ids:
                node = {
                    **node,
                    "properties": {
                        **(node.get("properties", {}) or {}),
                        "chunk_ids": chunk_ids,
                        "linked_row_ids": self._resolve_linked_rows(row_chunk_lookup, chunk_ids),
                    },
                }
                nodes.append(node)

        selected_node_ids = {node["id"] for node in nodes}
        edges = []
        for edge in graph.get("edges", []):
            chunk_ids = self._extract_graph_chunk_ids(edge.get("properties", {}))
            if set(chunk_ids) & all_chunk_ids:
                edges.append(
                    {
                        **edge,
                        "properties": {
                            **(edge.get("properties", {}) or {}),
                            "chunk_ids": chunk_ids,
                            "linked_row_ids": self._resolve_linked_rows(row_chunk_lookup, chunk_ids),
                        },
                    }
                )
                selected_node_ids.add(edge["source"])
                selected_node_ids.add(edge["target"])

        if not nodes and not edges:
            return self._empty_response("no_matching_graph_elements")

        nodes = [node for node in graph.get("nodes", []) if node["id"] in selected_node_ids]
        enriched_nodes = []
        for node in nodes:
            chunk_ids = self._extract_graph_chunk_ids(node.get("properties", {}))
            enriched_nodes.append(
                {
                    **node,
                    "properties": {
                        **(node.get("properties", {}) or {}),
                        "chunk_ids": chunk_ids,
                        "linked_row_ids": self._resolve_linked_rows(row_chunk_lookup, chunk_ids),
                    },
                }
            )

        enriched_nodes = self._limit_nodes(enriched_nodes, edges, max_nodes)
        allowed_node_ids = {node["id"] for node in enriched_nodes}
        edges = [edge for edge in edges if edge["source"] in allowed_node_ids and edge["target"] in allowed_node_ids]
        linked_row_ids = sorted(
            {
                row_id
                for item in [*enriched_nodes, *edges]
                for row_id in item.get("properties", {}).get("linked_row_ids", [])
            }
        )
        return view_models.AnswerGraphResponse(
            nodes=enriched_nodes,
            edges=edges,
            linked_row_ids=linked_row_ids,
            is_empty=False,
            empty_reason=None,
        )

    def _match_mirofish_rows_to_chunks(
        self,
        references: list[view_models.AnswerGraphReferenceInput],
        chunks: list[dict],
    ) -> dict[str, list[str]]:
        row_to_chunks: dict[str, list[str]] = {}
        normalized_chunks = [
            {
                **chunk,
                "_document_name_norm": _normalize_text(chunk.get("document_display_name", "")),
                "_content_norm": _normalize_text(chunk.get("content", "")),
            }
            for chunk in chunks
        ]

        for reference in references:
            direct_chunk_ids = _dedupe_preserve_order(reference.chunk_ids)
            if direct_chunk_ids:
                row_to_chunks[reference.source_row_id] = direct_chunk_ids
                continue

            text_norm = _normalize_text(reference.text or "")
            document_name_norm = _normalize_text(reference.document_name or "")
            if not text_norm:
                row_to_chunks[reference.source_row_id] = []
                continue

            matches: list[str] = []
            for chunk in normalized_chunks:
                if document_name_norm and chunk["_document_name_norm"] and chunk["_document_name_norm"] != document_name_norm:
                    continue
                chunk_text = chunk["_content_norm"]
                if not chunk_text:
                    continue
                if text_norm in chunk_text or chunk_text in text_norm:
                    matches.append(chunk["id"])

            if not matches and document_name_norm:
                for chunk in normalized_chunks:
                    chunk_text = chunk["_content_norm"]
                    if chunk_text and (text_norm in chunk_text or chunk_text in text_norm):
                        matches.append(chunk["id"])

            row_to_chunks[reference.source_row_id] = _dedupe_preserve_order(matches)

        return row_to_chunks

    @staticmethod
    def _extract_graph_chunk_ids(properties: dict) -> list[str]:
        return _dedupe_preserve_order(
            [
                *_split_source_ids(properties.get("chunk_ids")),
                *_split_source_ids(properties.get("source_chunk_id")),
                *_split_source_ids(properties.get("source_id")),
            ]
        )

    @staticmethod
    def _resolve_linked_rows(row_chunk_lookup: dict[str, set[str]], chunk_ids: list[str]) -> list[str]:
        if not chunk_ids:
            return []
        chunk_id_set = set(chunk_ids)
        return sorted(
            [
                row_id
                for row_id, row_chunk_ids in row_chunk_lookup.items()
                if row_chunk_ids & chunk_id_set
            ]
        )

    @staticmethod
    def _limit_nodes(nodes: list[dict], edges: list[dict], max_nodes: int) -> list[dict]:
        if len(nodes) <= max_nodes:
            return nodes

        degree_by_node: dict[str, int] = {node["id"]: 0 for node in nodes}
        for edge in edges:
            if edge["source"] in degree_by_node:
                degree_by_node[edge["source"]] += 1
            if edge["target"] in degree_by_node:
                degree_by_node[edge["target"]] += 1

        return sorted(
            nodes,
            key=lambda node: (
                -len(node.get("properties", {}).get("linked_row_ids", [])),
                -degree_by_node.get(node["id"], 0),
                str(node.get("properties", {}).get("entity_name") or node["id"]),
            ),
        )[:max_nodes]

    @staticmethod
    def _empty_response(reason: str) -> view_models.AnswerGraphResponse:
        return view_models.AnswerGraphResponse(
            nodes=[],
            edges=[],
            linked_row_ids=[],
            is_empty=True,
            empty_reason=reason,
        )


answer_graph_service = AnswerGraphService()
