from __future__ import annotations

import io
from types import SimpleNamespace

import pytest

from aperag.db import models as db_models
from aperag.mirofish_graph.constants import (
    GRAPH_STATUS_BUILDING,
    GRAPH_STATUS_FAILED,
    GRAPH_STATUS_READY,
    GRAPH_STATUS_UPDATING,
    GRAPH_STATUS_WAITING_FOR_DOCUMENTS,
    MIROFISH_CREATION_MODE,
    MIROFISH_GRAPH_ENGINE,
)
from aperag.schema.utils import dumpCollectionConfig, parseCollectionConfig
from aperag.schema.view_models import CollectionConfig
from aperag.service.mirofish_graph_service import MiroFishGraphService


def _make_collection(
    *,
    graph_status: str = GRAPH_STATUS_WAITING_FOR_DOCUMENTS,
    graph_revision: int = 0,
    active_graph_id: str | None = None,
):
    config = CollectionConfig(
        source='system',
        enable_vector=True,
        enable_fulltext=True,
        enable_knowledge_graph=False,
        enable_summary=False,
        enable_vision=False,
        language='zh-CN',
        creation_mode=MIROFISH_CREATION_MODE,
        graph_engine=MIROFISH_GRAPH_ENGINE,
        graph_status=graph_status,
        graph_status_message='',
        graph_revision=graph_revision,
        active_graph_id=active_graph_id,
    )
    return SimpleNamespace(
        id='col_001',
        user='user_001',
        status=db_models.CollectionStatus.ACTIVE,
        title='Test KB',
        description='intent',
        config=dumpCollectionConfig(config),
    )


class _FakeScalarResult:
    def __init__(self, collection):
        self._collection = collection

    def first(self):
        return self._collection


class _FakeAsyncExecuteResult:
    def __init__(self, collection):
        self._collection = collection

    def scalars(self):
        return _FakeScalarResult(self._collection)


class _FakeAsyncSession:
    def __init__(self, collection):
        self.collection = collection
        self.added = []
        self.flushed = False

    async def execute(self, stmt):  # noqa: ARG002
        return _FakeAsyncExecuteResult(self.collection)

    def add(self, instance):
        self.added.append(instance)

    async def flush(self):
        self.flushed = True


class _FakeAsyncDbOps:
    def __init__(self, session):
        self.session = session

    async def execute_with_transaction(self, callback):
        return await callback(self.session)


class _FakeSyncSession:
    def __init__(self, collection):
        self.collection = collection
        self.committed = False
        self.added = []

    def get(self, model, collection_id):  # noqa: ARG002
        if collection_id == self.collection.id:
            return self.collection
        return None

    def add(self, instance):
        self.added.append(instance)

    def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_prepare_graph_build_marks_first_build_as_building():
    collection = _make_collection()
    service = MiroFishGraphService()
    service.db_ops = _FakeAsyncDbOps(_FakeAsyncSession(collection))

    revision = await service.prepare_graph_build('user_001', 'col_001')

    assert revision == 1
    updated_config = parseCollectionConfig(collection.config)
    assert updated_config.graph_revision == 1
    assert updated_config.graph_status == GRAPH_STATUS_BUILDING
    assert updated_config.graph_error is None


@pytest.mark.asyncio
async def test_prepare_graph_build_marks_followup_build_as_updating():
    collection = _make_collection(
        graph_status=GRAPH_STATUS_READY,
        graph_revision=1,
        active_graph_id='graph_active',
    )
    service = MiroFishGraphService()
    service.db_ops = _FakeAsyncDbOps(_FakeAsyncSession(collection))

    revision = await service.prepare_graph_build('user_001', 'col_001')

    assert revision == 2
    updated_config = parseCollectionConfig(collection.config)
    assert updated_config.graph_revision == 2
    assert updated_config.graph_status == GRAPH_STATUS_UPDATING


def test_finalize_success_ignores_stale_revision(monkeypatch: pytest.MonkeyPatch):
    collection = _make_collection(
        graph_status=GRAPH_STATUS_UPDATING,
        graph_revision=3,
        active_graph_id='graph_old',
    )
    fake_session = _FakeSyncSession(collection)
    service = MiroFishGraphService()

    monkeypatch.setattr(
        'aperag.service.mirofish_graph_service.get_sync_session',
        lambda: iter([fake_session]),
    )

    result = service._finalize_success('col_001', 2, 'graph_new')

    assert result is False
    assert fake_session.committed is False
    updated_config = parseCollectionConfig(collection.config)
    assert updated_config.active_graph_id == 'graph_old'


def test_finalize_failure_marks_current_revision_failed(monkeypatch: pytest.MonkeyPatch):
    collection = _make_collection(
        graph_status=GRAPH_STATUS_UPDATING,
        graph_revision=4,
        active_graph_id='graph_active',
    )
    fake_session = _FakeSyncSession(collection)
    service = MiroFishGraphService()

    monkeypatch.setattr(
        'aperag.service.mirofish_graph_service.get_sync_session',
        lambda: iter([fake_session]),
    )

    result = service._finalize_failure('col_001', 4, 'boom')

    assert result is True
    assert fake_session.committed is True
    updated_config = parseCollectionConfig(collection.config)
    assert updated_config.graph_status == GRAPH_STATUS_FAILED
    assert updated_config.graph_error == 'boom'
    assert updated_config.active_graph_id == 'graph_active'


@pytest.mark.asyncio
async def test_get_knowledge_graph_maps_mirofish_nodes_and_edges():
    service = MiroFishGraphService()

    async def fake_load_graph_data(user_id: str, collection_id: str):  # noqa: ARG001
        return {
            'nodes': [
                {
                    'uuid': 'node-1',
                    'name': 'Alice',
                    'labels': ['Entity', 'Person'],
                    'summary': 'Person summary',
                    'aliases': ['A'],
                    'attributes': {'role': 'Analyst'},
                    'created_at': '2026-03-21T00:00:00Z',
                },
                {
                    'uuid': 'node-2',
                    'name': 'Acme',
                    'labels': ['Entity', 'Organization'],
                    'summary': 'Org summary',
                    'aliases': [],
                    'attributes': {'industry': 'Tech'},
                    'created_at': '2026-03-21T00:00:00Z',
                },
            ],
            'edges': [
                {
                    'uuid': 'edge-1',
                    'fact_type': 'WORKS_FOR',
                    'fact': 'Alice works for Acme.',
                    'evidence': 'Alice joined Acme.',
                    'confidence': 0.9,
                    'source_node_uuid': 'node-1',
                    'target_node_uuid': 'node-2',
                    'attributes': {'since': '2024'},
                    'created_at': '2026-03-21T00:00:00Z',
                }
            ],
        }

    service._load_graph_data = fake_load_graph_data  # type: ignore[method-assign]

    labels = await service.get_graph_labels('user_001', 'col_001')
    graph = await service.get_knowledge_graph('user_001', 'col_001', max_nodes=10)

    assert labels.labels == ['Organization', 'Person']
    assert graph['nodes'][0]['id'] == 'node-1'
    assert graph['nodes'][0]['properties']['entity_name'] == 'Alice'
    assert graph['nodes'][1]['properties']['entity_type'] == 'Organization'
    assert graph['edges'][0]['properties']['description'] == 'Alice works for Acme.'
    assert graph['edges'][0]['properties']['since'] == '2024'


def test_collect_document_texts_prefers_cached_markdown(monkeypatch: pytest.MonkeyPatch):
    service = MiroFishGraphService()
    collection = _make_collection()
    document = SimpleNamespace(
        id='doc_001',
        name='Cached Doc',
        object_store_base_path=lambda: 'user-001/col_001/doc_001',
    )

    class _FakeStore:
        def get(self, path: str):
            assert path == 'user-001/col_001/doc_001/parsed.md'
            return io.BytesIO('cached markdown'.encode('utf-8'))

    monkeypatch.setattr(
        'aperag.service.mirofish_graph_service.get_object_store',
        lambda: _FakeStore(),
    )
    monkeypatch.setattr(
        'aperag.service.mirofish_graph_service.parse_document_content',
        lambda *args, **kwargs: pytest.fail('should not parse when cached markdown exists'),
    )

    sections, texts = service._collect_document_texts(collection, [document])

    assert texts == ['cached markdown']
    assert sections == ['=== Cached Doc ===\ncached markdown']


def test_collect_document_texts_falls_back_to_parser_when_cache_missing(monkeypatch: pytest.MonkeyPatch):
    service = MiroFishGraphService()
    collection = _make_collection()
    document = SimpleNamespace(
        id='doc_002',
        name='Fallback Doc',
        object_store_base_path=lambda: 'user-001/col_001/doc_002',
    )
    local_doc = SimpleNamespace(path='C:/tmp/fallback.md')
    cleanup_calls: list[str] = []

    class _FakeStore:
        def get(self, path: str):
            assert path == 'user-001/col_001/doc_002/parsed.md'
            return None

    monkeypatch.setattr(
        'aperag.service.mirofish_graph_service.get_object_store',
        lambda: _FakeStore(),
    )
    monkeypatch.setattr(
        'aperag.service.mirofish_graph_service.parse_document_content',
        lambda *args, **kwargs: ('parsed from source', [], local_doc),
    )
    monkeypatch.setattr(
        'aperag.service.mirofish_graph_service.cleanup_local_document',
        lambda doc, _collection: cleanup_calls.append(doc.path),
    )

    sections, texts = service._collect_document_texts(collection, [document])

    assert texts == ['parsed from source']
    assert sections == ['=== Fallback Doc ===\nparsed from source']
    assert cleanup_calls == ['C:/tmp/fallback.md']
