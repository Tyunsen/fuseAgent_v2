from types import SimpleNamespace

import pytest

import sys
import types

sys.modules.pop("aperag.service.answer_graph_service", None)

collection_service_stub = types.ModuleType("aperag.service.collection_service")
collection_service_stub.collection_service = object()
graph_service_stub = types.ModuleType("aperag.service.graph_service")
graph_service_stub.graph_service = object()
mirofish_service_stub = types.ModuleType("aperag.service.mirofish_graph_service")
mirofish_service_stub.mirofish_graph_service = object()
sys.modules.setdefault("aperag.service.collection_service", collection_service_stub)
sys.modules.setdefault("aperag.service.graph_service", graph_service_stub)
sys.modules.setdefault("aperag.service.mirofish_graph_service", mirofish_service_stub)

from aperag.mirofish_graph.constants import MIROFISH_CREATION_MODE, MIROFISH_GRAPH_ENGINE
from aperag.schema.view_models import (
    AnswerGraphReferenceInput,
    AnswerGraphRequest,
    CollectionConfig,
    TraceConclusion,
    TraceSupportReferenceInput,
)
from aperag.service.answer_graph_service import AnswerGraphService


def _make_mirofish_collection():
    return SimpleNamespace(
        id="col_001",
        config=CollectionConfig(
            creation_mode=MIROFISH_CREATION_MODE,
            graph_engine=MIROFISH_GRAPH_ENGINE,
            language="zh-CN",
        ),
    )


class _FakeCollectionService:
    async def get_collection(self, user_id: str, collection_id: str):  # noqa: ARG002
        return _make_mirofish_collection()


class _FakeMiroFishGraphService:
    async def get_graph_snapshot(self, user_id: str, collection_id: str):  # noqa: ARG002
        return {
            "nodes": [
                {
                    "uuid": "node_1",
                    "name": "Mojtaba Khamenei",
                    "labels": ["Entity", "Person"],
                    "summary": "Leader",
                    "aliases": [],
                    "attributes": {},
                    "chunk_ids": ["chunk_a"],
                    "created_at": "2026-03-21T00:00:00Z",
                },
                {
                    "uuid": "node_2",
                    "name": "Iran",
                    "labels": ["Entity", "Organization"],
                    "summary": "Country",
                    "aliases": [],
                    "attributes": {},
                    "chunk_ids": ["chunk_b"],
                    "created_at": "2026-03-21T00:00:00Z",
                },
            ],
            "edges": [
                {
                    "uuid": "edge_1",
                    "fact_type": "LEADS",
                    "fact": "Mojtaba Khamenei leads Iran.",
                    "evidence": "Mojtaba Khamenei became the new leader.",
                    "confidence": 0.9,
                    "source_node_uuid": "node_1",
                    "target_node_uuid": "node_2",
                    "source_chunk_id": "chunk_a",
                    "attributes": {},
                    "created_at": "2026-03-21T00:00:00Z",
                }
            ],
            "chunks": [
                {
                    "id": "chunk_a",
                    "document_id": "graph_doc_1",
                    "document_display_name": "iran-update.pdf",
                    "chunk_index": 0,
                    "content": "Mojtaba Khamenei became the new leader in March.",
                },
                {
                    "id": "chunk_b",
                    "document_id": "graph_doc_1",
                    "document_display_name": "iran-update.pdf",
                    "chunk_index": 1,
                    "content": "Iran continued adjusting its leadership structure.",
                },
            ],
        }

    def _map_graph_node(self, node: dict) -> dict:
        return {
            "id": node["uuid"],
            "labels": node["labels"],
            "properties": {
                "entity_id": node["uuid"],
                "entity_name": node["name"],
                "entity_type": node["labels"][-1],
                "description": node.get("summary", ""),
            },
        }

    def _map_graph_edge(self, edge: dict) -> dict:
        return {
            "id": edge["uuid"],
            "type": edge["fact_type"],
            "source": edge["source_node_uuid"],
            "target": edge["target_node_uuid"],
            "properties": {
                "description": edge["fact"],
                "source_chunk_id": edge["source_chunk_id"],
            },
        }


@pytest.mark.asyncio
async def test_answer_graph_service_matches_mirofish_chunks_from_reference_text():
    service = AnswerGraphService()
    service.collection_service = _FakeCollectionService()
    service.mirofish_graph_service = _FakeMiroFishGraphService()

    response = await service.get_answer_graph(
        "user_001",
        "col_001",
        AnswerGraphRequest(
            references=[
                AnswerGraphReferenceInput(
                    source_row_id="row_1",
                    text="Mojtaba Khamenei became the new leader in March.",
                    document_name="iran-update.pdf",
                )
            ],
            max_nodes=12,
        ),
    )

    assert response.is_empty is False
    assert len(response.nodes) == 2
    assert len(response.edges) == 1
    assert response.nodes[0].properties.linked_row_ids == ["row_1"]
    assert response.edges[0].properties.linked_row_ids == ["row_1"]
    assert response.linked_row_ids == ["row_1"]


@pytest.mark.asyncio
async def test_answer_graph_service_returns_explicit_empty_state_when_no_graph_match():
    service = AnswerGraphService()
    service.collection_service = _FakeCollectionService()
    service.mirofish_graph_service = _FakeMiroFishGraphService()

    response = await service.get_answer_graph(
        "user_001",
        "col_001",
        AnswerGraphRequest(
            references=[
                AnswerGraphReferenceInput(
                    source_row_id="row_404",
                    text="Unrelated source fragment.",
                    document_name="iran-update.pdf",
                )
            ]
        ),
    )

    assert response.is_empty is True
    assert response.empty_reason == "no_matching_graph_elements"
    assert response.nodes == []
    assert response.edges == []


@pytest.mark.asyncio
async def test_trace_graph_service_builds_timeline_groups():
    service = AnswerGraphService()
    service.collection_service = _FakeCollectionService()
    service.mirofish_graph_service = _FakeMiroFishGraphService()

    response = await service.get_trace_graph(
        user_id="user_001",
        collection_id="col_001",
        references=[
            AnswerGraphReferenceInput(
                source_row_id="row_1",
                text="Mojtaba Khamenei became the new leader in March.",
                document_name="iran-update.pdf",
            )
        ],
        trace_mode="time",
        normalized_focus="2026-03",
        row_contexts=[
            TraceSupportReferenceInput(
                source_row_id="row_1",
                text="2026-03 joint exercise in Abu Dhabi.",
                chunk_ids=["chunk_a"],
                document_name="briefing.md",
                paragraph_precise=True,
            )
        ],
        conclusions=[
            TraceConclusion(
                id="conclusion_1",
                title="Time conclusion 1",
                statement="2026-03 joint exercise in Abu Dhabi.",
                source_row_ids=["row_1"],
                locator_quality="precise",
                time_label="2026-03",
            )
        ],
    )

    assert response.trace_mode == "time"
    assert response.layout == "timeline"
    assert response.groups
    assert response.groups[0].label == "2026-03"


@pytest.mark.asyncio
async def test_trace_graph_service_uses_force_layout_for_entity_mode():
    service = AnswerGraphService()
    service.collection_service = _FakeCollectionService()
    service.mirofish_graph_service = _FakeMiroFishGraphService()

    response = await service.get_trace_graph(
        user_id="user_001",
        collection_id="col_001",
        references=[
            AnswerGraphReferenceInput(
                source_row_id="row_1",
                text="Mojtaba Khamenei became the new leader in March.",
                document_name="iran-update.pdf",
            )
        ],
        trace_mode="entity",
        normalized_focus="Mojtaba Khamenei",
        row_contexts=[
            TraceSupportReferenceInput(
                source_row_id="row_1",
                text="Mojtaba Khamenei became the new leader in March.",
                chunk_ids=["chunk_a"],
                document_name="briefing.md",
                paragraph_precise=True,
            )
        ],
        conclusions=[
            TraceConclusion(
                id="conclusion_entity_1",
                title="Entity conclusion 1",
                statement="Mojtaba Khamenei became the new leader in March.",
                source_row_ids=["row_1"],
                locator_quality="precise",
                focus_entity="Mojtaba Khamenei",
            )
        ],
    )

    assert response.trace_mode == "entity"
    assert response.layout == "force"


@pytest.mark.asyncio
async def test_trace_graph_service_recovers_entity_graph_from_focus_signals_when_base_match_is_empty():
    service = AnswerGraphService()
    service.collection_service = _FakeCollectionService()
    service.mirofish_graph_service = _FakeMiroFishGraphService()

    response = await service.get_trace_graph(
        user_id="user_001",
        collection_id="col_001",
        references=[
            AnswerGraphReferenceInput(
                source_row_id="row_404",
                text="Unrelated source fragment.",
                document_name="iran-update.pdf",
            )
        ],
        trace_mode="entity",
        normalized_focus="Mojtaba Khamenei",
        row_contexts=[
            TraceSupportReferenceInput(
                source_row_id="row_404",
                text="Unrelated source fragment.",
                snippet="Leadership bargaining remained tense.",
                document_name="iran-update.pdf",
                preview_title="Leadership bargaining",
                chunk_ids=[],
                paragraph_precise=False,
            )
        ],
        conclusions=[
            TraceConclusion(
                id="conclusion_entity_fallback",
                title="Mojtaba Khamenei leadership role",
                statement="Mojtaba Khamenei shaped the latest leadership decisions.",
                source_row_ids=["row_404"],
                locator_quality="approximate",
                focus_entity="Mojtaba Khamenei",
            )
        ],
    )

    assert response.trace_mode == "entity"
    assert response.layout == "force"
    assert response.is_empty is False
    assert response.nodes
    assert response.edges
    assert "row_404" in response.linked_row_ids


@pytest.mark.asyncio
async def test_trace_graph_service_recovers_edges_when_base_entity_graph_only_has_nodes():
    service = AnswerGraphService()
    service.collection_service = _FakeCollectionService()
    service.mirofish_graph_service = _FakeMiroFishGraphService()

    response = await service.get_trace_graph(
        user_id="user_001",
        collection_id="col_001",
        references=[
            AnswerGraphReferenceInput(
                source_row_id="row_2",
                text="Iran continued adjusting its leadership structure.",
                document_name="iran-update.pdf",
                chunk_ids=["chunk_b"],
            )
        ],
        trace_mode="entity",
        normalized_focus="Iran",
        row_contexts=[
            TraceSupportReferenceInput(
                source_row_id="row_2",
                text="Iran continued adjusting its leadership structure.",
                document_name="iran-update.pdf",
                preview_title="Iran leadership structure",
                chunk_ids=["chunk_b"],
                paragraph_precise=True,
            )
        ],
        conclusions=[
            TraceConclusion(
                id="conclusion_entity_edges",
                title="Iran leadership structure",
                statement="Iran continued adjusting its leadership structure.",
                source_row_ids=["row_2"],
                locator_quality="precise",
                focus_entity="Iran",
            )
        ],
    )

    assert response.trace_mode == "entity"
    assert response.layout == "force"
    assert response.nodes
    assert response.edges
