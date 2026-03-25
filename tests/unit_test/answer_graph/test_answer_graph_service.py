from types import SimpleNamespace

import pytest

from aperag.mirofish_graph.constants import MIROFISH_CREATION_MODE, MIROFISH_GRAPH_ENGINE
from aperag.schema.view_models import AnswerGraphReferenceInput, AnswerGraphRequest, CollectionConfig
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
                    "name": "莫杰塔巴·哈梅内伊",
                    "labels": ["Entity", "Person"],
                    "summary": "新最高领袖",
                    "aliases": [],
                    "attributes": {},
                    "chunk_ids": ["chunk_a"],
                    "created_at": "2026-03-21T00:00:00Z",
                },
                {
                    "uuid": "node_2",
                    "name": "马苏德·佩泽希齐扬",
                    "labels": ["Entity", "Person"],
                    "summary": "总统",
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
                    "fact": "莫杰塔巴·哈梅内伊接任最高领袖。",
                    "evidence": "接任成为新最高领袖",
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
                    "document_display_name": "伊朗局势.pdf",
                    "chunk_index": 0,
                    "content": "莫杰塔巴·哈梅内伊成为新最高领袖，并开始主导局势。",
                },
                {
                    "id": "chunk_b",
                    "document_id": "graph_doc_1",
                    "document_display_name": "伊朗局势.pdf",
                    "chunk_index": 1,
                    "content": "马苏德·佩泽希齐扬继续担任伊朗总统。",
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
                "entity_type": "Person",
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
                    text="莫杰塔巴·哈梅内伊成为新最高领袖",
                    document_name="伊朗局势.pdf",
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
                    text="不存在的来源片段",
                    document_name="伊朗局势.pdf",
                )
            ]
        ),
    )

    assert response.is_empty is True
    assert response.empty_reason == "no_matching_graph_elements"
    assert response.nodes == []
    assert response.edges == []
