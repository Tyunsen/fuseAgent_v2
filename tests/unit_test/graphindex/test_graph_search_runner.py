from types import SimpleNamespace

import pytest

from aperag.flow.runners.graph_search import GraphSearchRepository, GraphSearchService
from aperag.mirofish_graph.constants import MIROFISH_CREATION_MODE, MIROFISH_GRAPH_ENGINE
from aperag.schema.utils import dumpCollectionConfig
from aperag.schema.view_models import CollectionConfig


class _FakeRepository(GraphSearchRepository):
    async def get_collection(self, user, collection_id: str):  # noqa: ARG002
        return SimpleNamespace(
            id=collection_id,
            config=dumpCollectionConfig(
                CollectionConfig(
                    enable_knowledge_graph=False,
                    creation_mode=MIROFISH_CREATION_MODE,
                    graph_engine=MIROFISH_GRAPH_ENGINE,
                    active_graph_id="graph_001",
                )
            ),
        )


@pytest.mark.asyncio
async def test_mirofish_collection_graph_search_returns_context_even_without_legacy_flag(monkeypatch):
    from aperag.service import mirofish_graph_service as mirofish_graph_service_module

    async def _fake_get_graph_snapshot(user_id: str, collection_id: str):  # noqa: ARG001
        return {
            "nodes": [
                {
                    "uuid": "node_1",
                    "name": "莫杰塔巴·哈梅内伊",
                    "labels": ["Entity", "Person"],
                    "summary": "伊朗新最高领袖",
                    "chunk_ids": ["chunk_1"],
                },
                {
                    "uuid": "node_2",
                    "name": "马苏德·佩泽希齐扬",
                    "labels": ["Entity", "Person"],
                    "summary": "伊朗总统",
                    "chunk_ids": ["chunk_2"],
                },
            ],
            "edges": [
                {
                    "uuid": "edge_1",
                    "fact_type": "LEADS",
                    "fact": "莫杰塔巴·哈梅内伊成为伊朗新最高领袖",
                    "evidence": "伊朗新领导层形成",
                    "confidence": 0.91,
                    "source_node_uuid": "node_1",
                    "target_node_uuid": "node_2",
                    "source_name": "莫杰塔巴·哈梅内伊",
                    "target_name": "马苏德·佩泽希齐扬",
                    "source_chunk_id": "chunk_1",
                }
            ],
            "chunks": [
                {
                    "id": "chunk_1",
                    "document_display_name": "05.md",
                    "content": "莫杰塔巴·哈梅内伊成为伊朗新最高领袖。",
                },
                {
                    "id": "chunk_2",
                    "document_display_name": "06.md",
                    "content": "马苏德·佩泽希齐扬继续担任伊朗总统。",
                },
            ],
        }

    monkeypatch.setattr(
        mirofish_graph_service_module.mirofish_graph_service,
        "get_graph_snapshot",
        _fake_get_graph_snapshot,
    )

    service = GraphSearchService(_FakeRepository())
    docs = await service.execute_graph_search(
        user="user_001",
        query="伊朗领导人 最高领袖 总统",
        top_k=5,
        collection_ids=["col_001"],
    )

    assert len(docs) == 1
    assert docs[0].metadata == {"recall_type": "graph_search"}
    assert "Entities(KG):" in docs[0].text
    assert "Relationships(KG):" in docs[0].text
    assert "Document Chunks(DC):" in docs[0].text
    assert "莫杰塔巴·哈梅内伊" in docs[0].text
    assert "马苏德·佩泽希齐扬" in docs[0].text
