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
from aperag.mirofish_graph.graph_identity import graph_key
from aperag.schema.utils import dumpCollectionConfig, parseCollectionConfig
from aperag.schema.view_models import CollectionConfig
from aperag.service.mirofish_graph_service import MiroFishGraphService


def _make_collection(
    *,
    graph_status: str = GRAPH_STATUS_WAITING_FOR_DOCUMENTS,
    graph_revision: int = 0,
    active_graph_id: str | None = None,
    active_graph_revision: int | None = None,
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
        active_graph_revision=active_graph_revision,
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


class _FakeSyncDbOps:
    def __init__(self, collection):
        self.collection = collection

    def query_collection_by_id(self, collection_id):
        if collection_id == self.collection.id:
            return self.collection
        return None


class _FakeOntologyGenerator:
    def __init__(self, ontology=None):
        self.ontology = ontology or {'entity_types': [{'name': 'Person'}], 'edge_types': [{'name': 'RELATED_TO'}]}
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        return self.ontology


class _FakeGraphBackend:
    def __init__(self):
        self.metadata = {
            'graph_id': 'graph_active',
            'project_id': 'col_001:r1',
            'name': 'Test KB r1',
            'description': 'MiroFish Neo4j graph',
            'ontology': {'entity_types': [{'name': 'Person'}], 'edge_types': [{'name': 'RELATED_TO'}]},
        }
        self.documents = []
        self.graph_data = {'node_count': 2, 'edge_count': 1, 'chunk_count': 3}
        self.build_calls = []
        self.append_calls = []
        self.deleted_graph_id = None

    def build_graph(self, **kwargs):
        self.build_calls.append(kwargs)
        return self.graph_data

    def append_documents(self, **kwargs):
        self.append_calls.append(kwargs)
        return self.graph_data

    def get_graph_metadata(self, graph_id: str):
        assert graph_id == self.metadata['graph_id']
        return self.metadata

    def get_graph_documents(self, graph_id: str):
        assert graph_id == self.metadata['graph_id']
        return list(self.documents)

    def get_graph_data(self, graph_id: str):
        assert graph_id == self.metadata['graph_id']
        return self.graph_data

    def delete_graph(self, graph_id: str):
        self.deleted_graph_id = graph_id


def _make_document(name: str):
    return SimpleNamespace(
        id=f'doc_{name.replace(" ", "_").lower()}',
        name=name,
        status=db_models.DocumentStatus.COMPLETE,
        object_store_base_path=lambda: f'user-001/col_001/{name}',
    )


def test_get_document_graph_statuses_marks_active_and_pending_documents(monkeypatch: pytest.MonkeyPatch):
    collection = _make_collection(
        graph_status=GRAPH_STATUS_UPDATING,
        graph_revision=2,
        active_graph_id='graph_active',
    )
    service = MiroFishGraphService()
    fake_backend = _FakeGraphBackend()
    fake_backend.documents = [
        {'filename': 'Existing Doc', 'display_name': 'Existing Doc', 'content_checksum': 'abc'}
    ]

    monkeypatch.setattr(
        'aperag.service.mirofish_graph_service.Neo4jGraphBackend',
        lambda extractor=None: fake_backend,
    )

    statuses = service.get_document_graph_statuses(
        collection,
        [_make_document('Existing Doc'), _make_document('New Doc')],
    )

    assert statuses['doc_existing_doc'] == db_models.DocumentIndexStatus.ACTIVE.value
    assert statuses['doc_new_doc'] == db_models.DocumentIndexStatus.CREATING.value


def test_get_document_graph_statuses_marks_uncovered_documents_failed_after_failed_update(
    monkeypatch: pytest.MonkeyPatch,
):
    collection = _make_collection(
        graph_status=GRAPH_STATUS_FAILED,
        graph_revision=2,
        active_graph_id='graph_active',
    )
    service = MiroFishGraphService()
    fake_backend = _FakeGraphBackend()
    fake_backend.documents = [
        {'filename': 'Existing Doc', 'display_name': 'Existing Doc', 'content_checksum': 'abc'}
    ]

    monkeypatch.setattr(
        'aperag.service.mirofish_graph_service.Neo4jGraphBackend',
        lambda extractor=None: fake_backend,
    )

    statuses = service.get_document_graph_statuses(
        collection,
        [_make_document('Existing Doc'), _make_document('New Doc')],
    )

    assert statuses['doc_existing_doc'] == db_models.DocumentIndexStatus.ACTIVE.value
    assert statuses['doc_new_doc'] == db_models.DocumentIndexStatus.FAILED.value


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


def test_build_graph_for_collection_uses_initial_build_when_no_active_graph(monkeypatch: pytest.MonkeyPatch):
    collection = _make_collection()
    collection.description = 'intent'
    service = MiroFishGraphService()
    service.sync_db_ops = _FakeSyncDbOps(collection)
    service._build_llm_client = lambda *_args, **_kwargs: object()  # type: ignore[method-assign]
    service._load_confirmed_documents = lambda _collection: [_make_document('Initial Doc')]  # type: ignore[method-assign]
    service._collect_document_payloads = lambda _collection, _documents: [  # type: ignore[method-assign]
        {'filename': 'Initial Doc', 'content': 'initial content'}
    ]

    fake_backend = _FakeGraphBackend()
    fake_ontology = _FakeOntologyGenerator()
    fake_session = _FakeSyncSession(collection)

    monkeypatch.setattr('aperag.service.mirofish_graph_service.ChunkGraphExtractor', lambda client: object())
    monkeypatch.setattr('aperag.service.mirofish_graph_service.Neo4jGraphBackend', lambda extractor: fake_backend)
    monkeypatch.setattr('aperag.service.mirofish_graph_service.OntologyGenerator', lambda client: fake_ontology)
    monkeypatch.setattr('aperag.service.mirofish_graph_service.get_sync_session', lambda: iter([fake_session]))

    result = service.build_graph_for_collection('col_001', 1)

    assert len(fake_backend.build_calls) == 1
    assert fake_backend.append_calls == []
    assert fake_ontology.calls[0]['document_texts'] == ['initial content']
    assert result['graph_id'] == graph_key('col_001:r1')
    updated_config = parseCollectionConfig(collection.config)
    assert updated_config.active_graph_id == graph_key('col_001:r1')
    assert updated_config.active_graph_revision == 1


def test_build_graph_for_collection_skips_stale_revision_before_loading_documents():
    collection = _make_collection(
        graph_status=GRAPH_STATUS_UPDATING,
        graph_revision=3,
        active_graph_id='graph_active',
        active_graph_revision=2,
    )
    service = MiroFishGraphService()
    service.sync_db_ops = _FakeSyncDbOps(collection)
    service._load_confirmed_documents = lambda *_args, **_kwargs: pytest.fail(  # type: ignore[method-assign]
        'should not load documents for a stale revision'
    )

    result = service.build_graph_for_collection('col_001', 2)

    assert result['skipped'] is True
    assert result['stale'] is True
    assert result['reason'] == 'stale'
    assert result['graph_id'] == 'graph_active'
    assert result['stage'] == 'preflight'


def test_build_graph_for_collection_skips_already_synchronized_revision_before_loading_documents():
    collection = _make_collection(
        graph_status=GRAPH_STATUS_READY,
        graph_revision=2,
        active_graph_id='graph_active',
        active_graph_revision=2,
    )
    service = MiroFishGraphService()
    service.sync_db_ops = _FakeSyncDbOps(collection)
    service._load_confirmed_documents = lambda *_args, **_kwargs: pytest.fail(  # type: ignore[method-assign]
        'should not load documents for an already synchronized revision'
    )

    result = service.build_graph_for_collection('col_001', 2)

    assert result['skipped'] is True
    assert result['already_synchronized'] is True
    assert result['reason'] == 'already_synchronized'
    assert result['graph_id'] == 'graph_active'
    assert result['stage'] == 'preflight'


def test_build_graph_for_collection_appends_only_missing_documents(monkeypatch: pytest.MonkeyPatch):
    collection = _make_collection(
        graph_status=GRAPH_STATUS_READY,
        graph_revision=1,
        active_graph_id='graph_active',
    )
    collection.description = 'intent'
    service = MiroFishGraphService()
    service.sync_db_ops = _FakeSyncDbOps(collection)
    service._build_llm_client = lambda *_args, **_kwargs: object()  # type: ignore[method-assign]
    service._load_confirmed_documents = lambda _collection: [  # type: ignore[method-assign]
        _make_document('Existing Doc'),
        _make_document('New Doc'),
    ]
    service._collect_document_payloads = lambda _collection, documents: [  # type: ignore[method-assign]
        {'filename': document.name, 'content': f'{document.name} content'} for document in documents
    ]

    fake_backend = _FakeGraphBackend()
    fake_backend.documents = [{'filename': 'Existing Doc', 'display_name': 'Existing Doc', 'content_checksum': 'abc'}]
    fake_ontology = _FakeOntologyGenerator()
    fake_session = _FakeSyncSession(collection)

    monkeypatch.setattr('aperag.service.mirofish_graph_service.ChunkGraphExtractor', lambda client: object())
    monkeypatch.setattr('aperag.service.mirofish_graph_service.Neo4jGraphBackend', lambda extractor: fake_backend)
    monkeypatch.setattr('aperag.service.mirofish_graph_service.OntologyGenerator', lambda client: fake_ontology)
    monkeypatch.setattr('aperag.service.mirofish_graph_service.get_sync_session', lambda: iter([fake_session]))

    result = service.build_graph_for_collection('col_001', 2)

    assert fake_backend.build_calls == []
    assert len(fake_backend.append_calls) == 1
    assert fake_backend.append_calls[0]['graph_id'] == 'graph_active'
    assert fake_backend.append_calls[0]['documents'] == [{'filename': 'New Doc', 'content': 'New Doc content'}]
    assert fake_backend.append_calls[0]['ontology'] == fake_backend.metadata['ontology']
    assert fake_ontology.calls == []
    assert result['incremental'] is True
    updated_config = parseCollectionConfig(collection.config)
    assert updated_config.active_graph_id == 'graph_active'
    assert updated_config.active_graph_revision == 2


def test_build_graph_for_collection_skips_when_request_becomes_stale_before_incremental_payloads(
    monkeypatch: pytest.MonkeyPatch,
):
    collection = _make_collection(
        graph_status=GRAPH_STATUS_READY,
        graph_revision=2,
        active_graph_id='graph_active',
        active_graph_revision=2,
    )
    stale_collection = _make_collection(
        graph_status=GRAPH_STATUS_UPDATING,
        graph_revision=3,
        active_graph_id='graph_active',
        active_graph_revision=2,
    )
    service = MiroFishGraphService()
    service.sync_db_ops = _FakeSyncDbOps(collection)
    service._build_llm_client = lambda *_args, **_kwargs: object()  # type: ignore[method-assign]
    service._load_confirmed_documents = lambda _collection: [  # type: ignore[method-assign]
        _make_document('Existing Doc'),
        _make_document('New Doc'),
    ]
    service._collect_document_payloads = lambda *_args, **_kwargs: pytest.fail(  # type: ignore[method-assign]
        'should not collect payloads after the request becomes stale'
    )

    fake_backend = _FakeGraphBackend()
    fake_backend.documents = [{'filename': 'Existing Doc', 'display_name': 'Existing Doc', 'content_checksum': 'abc'}]

    states = iter(
        [
            ('current', collection, parseCollectionConfig(collection.config)),
            ('stale', stale_collection, parseCollectionConfig(stale_collection.config)),
        ]
    )

    monkeypatch.setattr('aperag.service.mirofish_graph_service.ChunkGraphExtractor', lambda client: object())
    monkeypatch.setattr('aperag.service.mirofish_graph_service.Neo4jGraphBackend', lambda extractor: fake_backend)
    monkeypatch.setattr(
        service,
        '_get_request_state',
        lambda *_args, **_kwargs: next(states),
    )

    result = service.build_graph_for_collection('col_001', 2)

    assert result['skipped'] is True
    assert result['stale'] is True
    assert result['reason'] == 'stale'
    assert result['stage'] == 'before_incremental_payloads'


def test_build_graph_for_collection_short_circuits_when_no_new_documents(monkeypatch: pytest.MonkeyPatch):
    collection = _make_collection(
        graph_status=GRAPH_STATUS_READY,
        graph_revision=1,
        active_graph_id='graph_active',
    )
    service = MiroFishGraphService()
    service.sync_db_ops = _FakeSyncDbOps(collection)
    service._build_llm_client = lambda *_args, **_kwargs: object()  # type: ignore[method-assign]
    service._load_confirmed_documents = lambda _collection: [_make_document('Existing Doc')]  # type: ignore[method-assign]
    service._collect_document_payloads = lambda *_args, **_kwargs: pytest.fail('should not parse when there is no incremental work')  # type: ignore[method-assign]

    fake_backend = _FakeGraphBackend()
    fake_backend.documents = [{'filename': 'Existing Doc', 'display_name': 'Existing Doc', 'content_checksum': 'abc'}]
    fake_session = _FakeSyncSession(collection)

    monkeypatch.setattr('aperag.service.mirofish_graph_service.ChunkGraphExtractor', lambda client: object())
    monkeypatch.setattr('aperag.service.mirofish_graph_service.Neo4jGraphBackend', lambda extractor: fake_backend)
    monkeypatch.setattr('aperag.service.mirofish_graph_service.OntologyGenerator', lambda client: _FakeOntologyGenerator())
    monkeypatch.setattr('aperag.service.mirofish_graph_service.get_sync_session', lambda: iter([fake_session]))

    result = service.build_graph_for_collection('col_001', 2)

    assert fake_backend.build_calls == []
    assert fake_backend.append_calls == []
    assert result['no_changes'] is True
    updated_config = parseCollectionConfig(collection.config)
    assert updated_config.active_graph_id == 'graph_active'
    assert updated_config.active_graph_revision == 2


def test_build_graph_for_collection_short_circuits_when_incremental_documents_have_no_payloads(
    monkeypatch: pytest.MonkeyPatch,
):
    collection = _make_collection(
        graph_status=GRAPH_STATUS_READY,
        graph_revision=1,
        active_graph_id='graph_active',
    )
    service = MiroFishGraphService()
    service.sync_db_ops = _FakeSyncDbOps(collection)
    service._build_llm_client = lambda *_args, **_kwargs: object()  # type: ignore[method-assign]
    service._load_confirmed_documents = lambda _collection: [  # type: ignore[method-assign]
        _make_document('Existing Doc'),
        _make_document('New Doc'),
    ]
    service._collect_document_payloads = lambda _collection, _documents: []  # type: ignore[method-assign]

    fake_backend = _FakeGraphBackend()
    fake_backend.documents = [{'filename': 'Existing Doc', 'display_name': 'Existing Doc', 'content_checksum': 'abc'}]
    fake_session = _FakeSyncSession(collection)

    monkeypatch.setattr('aperag.service.mirofish_graph_service.ChunkGraphExtractor', lambda client: object())
    monkeypatch.setattr('aperag.service.mirofish_graph_service.Neo4jGraphBackend', lambda extractor: fake_backend)
    monkeypatch.setattr('aperag.service.mirofish_graph_service.OntologyGenerator', lambda client: _FakeOntologyGenerator())
    monkeypatch.setattr('aperag.service.mirofish_graph_service.get_sync_session', lambda: iter([fake_session]))

    result = service.build_graph_for_collection('col_001', 2)

    assert fake_backend.build_calls == []
    assert fake_backend.append_calls == []
    assert result['no_changes'] is True
    assert result['document_count'] == 1
    updated_config = parseCollectionConfig(collection.config)
    assert updated_config.active_graph_id == 'graph_active'
    assert updated_config.active_graph_revision == 2


def test_handle_build_failure_preserves_active_graph_after_incremental_append_error(
    monkeypatch: pytest.MonkeyPatch,
):
    collection = _make_collection(
        graph_status=GRAPH_STATUS_UPDATING,
        graph_revision=2,
        active_graph_id='graph_active',
    )
    service = MiroFishGraphService()
    service.sync_db_ops = _FakeSyncDbOps(collection)
    service._build_llm_client = lambda *_args, **_kwargs: object()  # type: ignore[method-assign]
    service._load_confirmed_documents = lambda _collection: [_make_document('New Doc')]  # type: ignore[method-assign]
    service._collect_document_payloads = lambda _collection, _documents: [  # type: ignore[method-assign]
        {'filename': 'New Doc', 'content': 'new content'}
    ]

    fake_backend = _FakeGraphBackend()
    fake_backend.documents = []
    fake_session = _FakeSyncSession(collection)

    def _raise_append(**_kwargs):
        raise RuntimeError('append boom')

    fake_backend.append_documents = _raise_append  # type: ignore[method-assign]

    monkeypatch.setattr('aperag.service.mirofish_graph_service.ChunkGraphExtractor', lambda client: object())
    monkeypatch.setattr('aperag.service.mirofish_graph_service.Neo4jGraphBackend', lambda extractor: fake_backend)
    monkeypatch.setattr('aperag.service.mirofish_graph_service.OntologyGenerator', lambda client: _FakeOntologyGenerator())
    monkeypatch.setattr('aperag.service.mirofish_graph_service.get_sync_session', lambda: iter([fake_session]))

    with pytest.raises(RuntimeError, match='append boom'):
        service.build_graph_for_collection('col_001', 2)

    service.handle_build_failure('col_001', 2, 'append boom')

    updated_config = parseCollectionConfig(collection.config)
    assert updated_config.graph_status == GRAPH_STATUS_FAILED
    assert updated_config.graph_error == 'append boom'
    assert updated_config.active_graph_id == 'graph_active'
