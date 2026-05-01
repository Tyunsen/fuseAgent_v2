from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Iterable

from aperag.mirofish_graph.helpers import is_mirofish_collection_config
from aperag.schema import view_models

logger = logging.getLogger(__name__)


SOURCE_ID_SPLIT_PATTERN = re.compile(r"(?:<SEP>|\|)")
TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9._-]*|[\u4e00-\u9fff]{2,}")


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

    async def get_trace_graph(
        self,
        *,
        user_id: str,
        collection_id: str,
        references: list[view_models.AnswerGraphReferenceInput],
        trace_mode: str = "default",
        normalized_focus: str | None = None,
        max_nodes: int = 18,
        row_contexts: list[view_models.TraceSupportReferenceInput] | None = None,
        conclusions: list[view_models.TraceConclusion] | None = None,
    ) -> view_models.AnswerGraphResponse:
        base_graph = await self.get_answer_graph(
            user_id=user_id,
            collection_id=collection_id,
            request=view_models.AnswerGraphRequest(
                references=references,
                max_nodes=max_nodes,
            ),
        )
        graph = base_graph.model_copy(deep=True)
        if trace_mode == "entity" and (graph.is_empty or not graph.edges):
            recovered_graph = await self._recover_entity_trace_graph(
                user_id=user_id,
                collection_id=collection_id,
                normalized_focus=normalized_focus,
                max_nodes=max_nodes,
                row_contexts=row_contexts or [],
                conclusions=conclusions or [],
            )
            if recovered_graph and not recovered_graph.is_empty and (
                len(recovered_graph.edges) >= len(graph.edges)
            ):
                graph = recovered_graph
        graph.trace_mode = trace_mode
        graph.layout = self._layout_for_trace_mode(trace_mode)
        graph.focus_label = normalized_focus
        graph.groups = self._build_trace_groups(
            graph=graph,
            trace_mode=trace_mode,
            normalized_focus=normalized_focus,
            row_contexts=row_contexts or [],
            conclusions=conclusions or [],
        )
        if graph.groups and graph.layout != "force":
            graph.is_empty = False
            graph.empty_reason = None
        return graph

    async def _recover_entity_trace_graph(
        self,
        *,
        user_id: str,
        collection_id: str,
        normalized_focus: str | None,
        max_nodes: int,
        row_contexts: list[view_models.TraceSupportReferenceInput],
        conclusions: list[view_models.TraceConclusion],
    ) -> view_models.AnswerGraphResponse | None:
        signals = self._build_entity_signals(normalized_focus, row_contexts, conclusions)
        if not signals:
            return None

        collection = await self.collection_service.get_collection(user_id, collection_id)
        if is_mirofish_collection_config(collection.config):
            return await self._recover_mirofish_entity_graph(
                user_id=user_id,
                collection_id=collection_id,
                signals=signals,
                max_nodes=max_nodes,
                row_contexts=row_contexts,
                conclusions=conclusions,
            )

        return await self._recover_standard_entity_graph(
            user_id=user_id,
            collection_id=collection_id,
            signals=signals,
            max_nodes=max_nodes,
            row_contexts=row_contexts,
            conclusions=conclusions,
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

    @staticmethod
    def _layout_for_trace_mode(trace_mode: str) -> str:
        return {
            "time": "timeline",
            "space": "location",
            "entity": "force",
        }.get(trace_mode, "force")

    def _build_trace_groups(
        self,
        *,
        graph: view_models.AnswerGraphResponse,
        trace_mode: str,
        normalized_focus: str | None,
        row_contexts: list[view_models.TraceSupportReferenceInput],
        conclusions: list[view_models.TraceConclusion],
    ) -> list[view_models.TraceGraphGroup]:
        row_to_node_ids: dict[str, list[str]] = defaultdict(list)
        for node in graph.nodes:
            for row_id in self._linked_row_ids(node.properties):
                row_to_node_ids[row_id].append(node.id)

        if trace_mode == "time":
            return self._build_time_groups(
                row_contexts=row_contexts,
                conclusions=conclusions,
                normalized_focus=normalized_focus,
                row_to_node_ids=row_to_node_ids,
            )
        if trace_mode == "space":
            return self._build_space_groups(
                row_contexts=row_contexts,
                conclusions=conclusions,
                normalized_focus=normalized_focus,
                row_to_node_ids=row_to_node_ids,
            )
        if trace_mode == "entity":
            return self._build_entity_groups(
                row_contexts=row_contexts,
                conclusions=conclusions,
                normalized_focus=normalized_focus,
                row_to_node_ids=row_to_node_ids,
            )
        if conclusions:
            return [
                view_models.TraceGraphGroup(
                    id=conclusion.id,
                    label=conclusion.title,
                    kind="default",
                    row_ids=list(conclusion.source_row_ids),
                    node_ids=self._collect_group_node_ids(
                        conclusion.source_row_ids,
                        row_to_node_ids,
                    ),
                )
                for conclusion in conclusions
                if conclusion.source_row_ids
            ]
        if row_contexts:
            row_ids = [row.source_row_id for row in row_contexts]
            return [
                view_models.TraceGraphGroup(
                    id="default-evidence",
                    label=normalized_focus or "Evidence",
                    kind="default",
                    row_ids=row_ids,
                    node_ids=self._collect_group_node_ids(row_ids, row_to_node_ids),
                )
            ]
        return []

    def _build_time_groups(
        self,
        *,
        row_contexts: list[view_models.TraceSupportReferenceInput],
        conclusions: list[view_models.TraceConclusion],
        normalized_focus: str | None,
        row_to_node_ids: dict[str, list[str]],
    ) -> list[view_models.TraceGraphGroup]:
        grouped: dict[str, dict[str, list[str]]] = {}
        for conclusion in conclusions:
            label = conclusion.time_label or normalized_focus or "Unspecified time"
            if not conclusion.source_row_ids:
                continue
            bucket = grouped.setdefault(label, {"row_ids": [], "node_ids": []})
            bucket["row_ids"].extend(conclusion.source_row_ids)
            bucket["node_ids"].extend(
                self._collect_group_node_ids(conclusion.source_row_ids, row_to_node_ids)
            )

        if not grouped:
            for row in row_contexts:
                label = self._extract_time_label(row.text or row.snippet or "") or normalized_focus or "Unspecified time"
                bucket = grouped.setdefault(label, {"row_ids": [], "node_ids": []})
                bucket["row_ids"].append(row.source_row_id)
                bucket["node_ids"].extend(
                    self._collect_group_node_ids([row.source_row_id], row_to_node_ids)
                )

        sorted_items = sorted(grouped.items(), key=lambda item: self._time_sort_key(item[0]))
        return [
            view_models.TraceGraphGroup(
                id=f"time-{index}",
                label=label,
                kind="time",
                row_ids=_dedupe_preserve_order(data["row_ids"]),
                node_ids=_dedupe_preserve_order(data["node_ids"]),
            )
            for index, (label, data) in enumerate(sorted_items, start=1)
        ]

    def _build_space_groups(
        self,
        *,
        row_contexts: list[view_models.TraceSupportReferenceInput],
        conclusions: list[view_models.TraceConclusion],
        normalized_focus: str | None,
        row_to_node_ids: dict[str, list[str]],
    ) -> list[view_models.TraceGraphGroup]:
        grouped: dict[str, dict[str, list[str]]] = {}
        for conclusion in conclusions:
            label = conclusion.place_label or normalized_focus or "Related place"
            if not conclusion.source_row_ids:
                continue
            bucket = grouped.setdefault(label, {"row_ids": [], "node_ids": []})
            bucket["row_ids"].extend(conclusion.source_row_ids)
            bucket["node_ids"].extend(
                self._collect_group_node_ids(conclusion.source_row_ids, row_to_node_ids)
            )

        if not grouped:
            for row in row_contexts:
                label = row.section_label or normalized_focus or row.document_name or "Related place"
                bucket = grouped.setdefault(label, {"row_ids": [], "node_ids": []})
                bucket["row_ids"].append(row.source_row_id)
                bucket["node_ids"].extend(
                    self._collect_group_node_ids([row.source_row_id], row_to_node_ids)
                )

        return [
            view_models.TraceGraphGroup(
                id=f"space-{index}",
                label=label,
                kind="space",
                row_ids=_dedupe_preserve_order(data["row_ids"]),
                node_ids=_dedupe_preserve_order(data["node_ids"]),
            )
            for index, (label, data) in enumerate(grouped.items(), start=1)
        ]

    def _build_entity_groups(
        self,
        *,
        row_contexts: list[view_models.TraceSupportReferenceInput],
        conclusions: list[view_models.TraceConclusion],
        normalized_focus: str | None,
        row_to_node_ids: dict[str, list[str]],
    ) -> list[view_models.TraceGraphGroup]:
        focus_label = normalized_focus or next(
            (conclusion.focus_entity for conclusion in conclusions if conclusion.focus_entity),
            None,
        ) or "Focus entity"
        groups: list[view_models.TraceGraphGroup] = []

        focus_row_ids = [
            row_id
            for conclusion in conclusions
            for row_id in conclusion.source_row_ids
            if conclusion.focus_entity == focus_label or not conclusion.focus_entity
        ]
        if not focus_row_ids:
            focus_row_ids = [row.source_row_id for row in row_contexts[:4]]
        groups.append(
            view_models.TraceGraphGroup(
                id="entity-focus",
                label=focus_label,
                kind="entity",
                row_ids=_dedupe_preserve_order(focus_row_ids),
                node_ids=self._collect_group_node_ids(focus_row_ids, row_to_node_ids),
            )
        )

        for index, conclusion in enumerate(conclusions, start=1):
            if not conclusion.source_row_ids:
                continue
            label = conclusion.focus_entity or conclusion.title
            if label == focus_label:
                continue
            groups.append(
                view_models.TraceGraphGroup(
                    id=f"entity-related-{index}",
                    label=label,
                    kind="entity",
                    row_ids=list(conclusion.source_row_ids),
                    node_ids=self._collect_group_node_ids(
                        conclusion.source_row_ids,
                        row_to_node_ids,
                    ),
                )
            )
        return groups

    async def _recover_mirofish_entity_graph(
        self,
        *,
        user_id: str,
        collection_id: str,
        signals: list[str],
        max_nodes: int,
        row_contexts: list[view_models.TraceSupportReferenceInput],
        conclusions: list[view_models.TraceConclusion],
    ) -> view_models.AnswerGraphResponse | None:
        graph_snapshot = await self.mirofish_graph_service.get_graph_snapshot(user_id, collection_id)
        nodes_snapshot = list(graph_snapshot.get("nodes") or [])
        edges_snapshot = list(graph_snapshot.get("edges") or [])
        if not nodes_snapshot:
            return None

        fallback_row_ids = self._fallback_row_ids(row_contexts, conclusions)
        row_chunk_lookup = {
            row.source_row_id: set(_dedupe_preserve_order(row.chunk_ids))
            for row in row_contexts
            if row.chunk_ids
        }

        scored_nodes = [
            (self._score_signal_match(self._mirofish_node_search_text(node), signals), node)
            for node in nodes_snapshot
        ]
        scored_nodes = [item for item in scored_nodes if item[0] > 0]
        scored_nodes.sort(key=lambda item: item[0], reverse=True)
        selected_node_ids: set[str] = {
            node["uuid"]
            for _, node in scored_nodes[: max(4, min(max_nodes, 8))]
        }

        selected_edges = []
        for edge in edges_snapshot:
            edge_score = self._score_signal_match(self._mirofish_edge_search_text(edge), signals)
            if edge_score > 0 or edge["source_node_uuid"] in selected_node_ids or edge["target_node_uuid"] in selected_node_ids:
                selected_edges.append(edge)
                selected_node_ids.add(edge["source_node_uuid"])
                selected_node_ids.add(edge["target_node_uuid"])

        if not selected_node_ids:
            return None

        selected_nodes = [node for node in nodes_snapshot if node["uuid"] in selected_node_ids]
        nodes = []
        for node in selected_nodes:
            mapped = self.mirofish_graph_service._map_graph_node(node)
            chunk_ids = _dedupe_preserve_order(_split_source_ids(node.get("chunk_ids")))
            linked_row_ids = self._resolve_linked_rows(row_chunk_lookup, chunk_ids) or fallback_row_ids
            mapped["properties"]["chunk_ids"] = chunk_ids
            mapped["properties"]["linked_row_ids"] = linked_row_ids
            nodes.append(mapped)

        edges = []
        for edge in selected_edges:
            mapped = self.mirofish_graph_service._map_graph_edge(edge)
            chunk_ids = _dedupe_preserve_order(_split_source_ids(edge.get("source_chunk_id")))
            linked_row_ids = self._resolve_linked_rows(row_chunk_lookup, chunk_ids) or fallback_row_ids
            mapped["properties"]["chunk_ids"] = chunk_ids
            mapped["properties"]["linked_row_ids"] = linked_row_ids
            edges.append(mapped)

        nodes = self._limit_nodes(nodes, edges, max_nodes)
        allowed_node_ids = {node["id"] for node in nodes}
        edges = [
            edge
            for edge in edges
            if edge["source"] in allowed_node_ids and edge["target"] in allowed_node_ids
        ]
        linked_row_ids = sorted(
            {
                row_id
                for item in [*nodes, *edges]
                for row_id in item.get("properties", {}).get("linked_row_ids", [])
            }
        )
        if not nodes:
            return None

        return view_models.AnswerGraphResponse(
            nodes=nodes,
            edges=edges,
            linked_row_ids=linked_row_ids or fallback_row_ids,
            is_empty=False,
            empty_reason=None,
        )

    async def _recover_standard_entity_graph(
        self,
        *,
        user_id: str,
        collection_id: str,
        signals: list[str],
        max_nodes: int,
        row_contexts: list[view_models.TraceSupportReferenceInput],
        conclusions: list[view_models.TraceConclusion],
    ) -> view_models.AnswerGraphResponse | None:
        graph_window = min(max(max_nodes * 8, 200), 2000)
        graph = await self.graph_service.get_knowledge_graph(
            user_id=user_id,
            collection_id=collection_id,
            label="*",
            max_depth=3,
            max_nodes=graph_window,
        )
        nodes_snapshot = list(graph.get("nodes") or [])
        edges_snapshot = list(graph.get("edges") or [])
        if not nodes_snapshot:
            return None

        fallback_row_ids = self._fallback_row_ids(row_contexts, conclusions)
        row_chunk_lookup = {
            row.source_row_id: set(_dedupe_preserve_order(row.chunk_ids))
            for row in row_contexts
            if row.chunk_ids
        }

        scored_nodes = [
            (self._score_signal_match(self._standard_node_search_text(node), signals), node)
            for node in nodes_snapshot
        ]
        scored_nodes = [item for item in scored_nodes if item[0] > 0]
        scored_nodes.sort(key=lambda item: item[0], reverse=True)
        selected_node_ids: set[str] = {
            node["id"]
            for _, node in scored_nodes[: max(4, min(max_nodes, 8))]
        }

        selected_edges = []
        for edge in edges_snapshot:
            edge_score = self._score_signal_match(self._standard_edge_search_text(edge), signals)
            if edge_score > 0 or edge["source"] in selected_node_ids or edge["target"] in selected_node_ids:
                selected_edges.append(edge)
                selected_node_ids.add(edge["source"])
                selected_node_ids.add(edge["target"])

        if not selected_node_ids:
            return None

        nodes = []
        for node in nodes_snapshot:
            if node["id"] not in selected_node_ids:
                continue
            chunk_ids = self._extract_graph_chunk_ids(node.get("properties", {}))
            linked_row_ids = self._resolve_linked_rows(row_chunk_lookup, chunk_ids) or fallback_row_ids
            nodes.append(
                {
                    **node,
                    "properties": {
                        **(node.get("properties", {}) or {}),
                        "chunk_ids": chunk_ids,
                        "linked_row_ids": linked_row_ids,
                    },
                }
            )

        edges = []
        for edge in selected_edges:
            chunk_ids = self._extract_graph_chunk_ids(edge.get("properties", {}))
            linked_row_ids = self._resolve_linked_rows(row_chunk_lookup, chunk_ids) or fallback_row_ids
            edges.append(
                {
                    **edge,
                    "properties": {
                        **(edge.get("properties", {}) or {}),
                        "chunk_ids": chunk_ids,
                        "linked_row_ids": linked_row_ids,
                    },
                }
            )

        nodes = self._limit_nodes(nodes, edges, max_nodes)
        allowed_node_ids = {node["id"] for node in nodes}
        edges = [
            edge
            for edge in edges
            if edge["source"] in allowed_node_ids and edge["target"] in allowed_node_ids
        ]
        linked_row_ids = sorted(
            {
                row_id
                for item in [*nodes, *edges]
                for row_id in item.get("properties", {}).get("linked_row_ids", [])
            }
        )
        if not nodes:
            return None

        return view_models.AnswerGraphResponse(
            nodes=nodes,
            edges=edges,
            linked_row_ids=linked_row_ids or fallback_row_ids,
            is_empty=False,
            empty_reason=None,
        )

    @staticmethod
    def _collect_group_node_ids(
        row_ids: Iterable[str],
        row_to_node_ids: dict[str, list[str]],
    ) -> list[str]:
        return _dedupe_preserve_order(
            [
                node_id
                for row_id in row_ids
                for node_id in row_to_node_ids.get(row_id, [])
            ]
        )

    @staticmethod
    def _build_entity_signals(
        normalized_focus: str | None,
        row_contexts: list[view_models.TraceSupportReferenceInput],
        conclusions: list[view_models.TraceConclusion],
    ) -> list[str]:
        candidates = [
            normalized_focus or "",
            *[conclusion.focus_entity or "" for conclusion in conclusions],
            *[conclusion.title or "" for conclusion in conclusions],
            *[conclusion.statement or "" for conclusion in conclusions],
            *[row.preview_title or "" for row in row_contexts],
            *[row.section_label or "" for row in row_contexts],
            *[row.document_name or "" for row in row_contexts],
        ]
        return _dedupe_preserve_order(
            [
                candidate.strip()
                for candidate in candidates
                if AnswerGraphService._is_useful_entity_signal(candidate)
            ]
        )

    @staticmethod
    def _is_useful_entity_signal(value: str) -> bool:
        candidate = str(value or "").strip()
        if len(candidate) < 2:
            return False
        lowered = candidate.lower()
        if lowered in {"focus entity", "related place", "evidence", "default", "entity", "time", "space"}:
            return False
        return not candidate.isdigit()

    @staticmethod
    def _score_signal_match(text: str, signals: list[str]) -> int:
        normalized_text = _normalize_text(text)
        if not normalized_text:
            return 0

        best_score = 0
        text_tokens = {token for token in TOKEN_PATTERN.findall(text or "") if token}
        for index, signal in enumerate(signals):
            normalized_signal = _normalize_text(signal)
            if not normalized_signal:
                continue
            score = 0
            if normalized_signal in normalized_text:
                score = 200 - index * 5 + len(normalized_signal)
            else:
                signal_tokens = {token for token in TOKEN_PATTERN.findall(signal or "") if token}
                overlap = len(signal_tokens & text_tokens)
                if overlap:
                    score = overlap * 20 - index
            if score > best_score:
                best_score = score
        return best_score

    @staticmethod
    def _mirofish_node_search_text(node: dict) -> str:
        return " ".join(
            filter(
                None,
                [
                    str(node.get("name") or ""),
                    " ".join(str(label) for label in node.get("labels") or []),
                    str(node.get("summary") or ""),
                    " ".join(str(alias) for alias in node.get("aliases") or []),
                ],
            )
        )

    @staticmethod
    def _mirofish_edge_search_text(edge: dict) -> str:
        return " ".join(
            filter(
                None,
                [
                    str(edge.get("fact_type") or ""),
                    str(edge.get("fact") or ""),
                    str(edge.get("evidence") or ""),
                ],
            )
        )

    @staticmethod
    def _standard_node_search_text(node: dict) -> str:
        properties = node.get("properties", {}) or {}
        return " ".join(
            filter(
                None,
                [
                    str(properties.get("entity_name") or node.get("id") or ""),
                    str(properties.get("description") or ""),
                    str(properties.get("entity_type") or ""),
                ],
            )
        )

    @staticmethod
    def _standard_edge_search_text(edge: dict) -> str:
        properties = edge.get("properties", {}) or {}
        return " ".join(
            filter(
                None,
                [
                    str(edge.get("type") or ""),
                    str(properties.get("description") or ""),
                ],
            )
        )

    @staticmethod
    def _fallback_row_ids(
        row_contexts: list[view_models.TraceSupportReferenceInput],
        conclusions: list[view_models.TraceConclusion],
    ) -> list[str]:
        return _dedupe_preserve_order(
            [
                *[row.source_row_id for row in row_contexts],
                *[
                    row_id
                    for conclusion in conclusions
                    for row_id in conclusion.source_row_ids
                ],
            ]
        )[:6]

    @staticmethod
    def _extract_time_label(text: str) -> str | None:
        match = re.search(
            r"\d{4}[年/-]\d{1,2}(?:[月/-]\d{1,2}日?)?|\d{4}年|\d{1,2}月",
            text or "",
        )
        return match.group(0) if match else None

    @staticmethod
    def _linked_row_ids(properties: object) -> list[str]:
        if isinstance(properties, dict):
            raw_value = properties.get("linked_row_ids", [])
        else:
            raw_value = getattr(properties, "linked_row_ids", [])
        if not isinstance(raw_value, list):
            return []
        return [str(value).strip() for value in raw_value if str(value).strip()]

    @staticmethod
    def _time_sort_key(label: str) -> tuple[int, str]:
        match = re.search(r"(\d{4})(?:[年/-](\d{1,2}))?", label or "")
        if not match:
            month_match = re.search(r"month:(\d{2})|(\d{1,2})月", label or "")
            if month_match:
                month_value = month_match.group(1) or month_match.group(2) or "99"
                return (9999, f"99-{int(month_value):02d}")
            return (9999, label or "")
        year = int(match.group(1))
        month = int(match.group(2) or 0)
        return (year, f"{month:02d}")


answer_graph_service = AnswerGraphService()
