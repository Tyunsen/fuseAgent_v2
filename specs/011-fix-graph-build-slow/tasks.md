# Tasks: MiroFish Graph Build Performance Optimization

**Input**: Design documents from `/specs/011-fix-graph-build-slow/`
**Prerequisites**: plan.md (required), spec.md (required)

**Tests**: Existing unit tests must continue passing after optimizations.

**Organization**: Tasks grouped by optimization target for independent implementation.

## Phase 1: Quick Wins (Independent, No Risk)

**Purpose**: Low-risk optimizations that can be applied independently.

- [ ] T001 Cache `ensure_ready()` schema checks in `Neo4jClientManager` — add `_schema_ready` flag, skip schema queries after first successful call.
- [ ] T002 Add `GRAPH_COUNTS_QUERY` to `neo4j_queries.py` — count-only aggregation query for nodes, edges, chunks.
- [ ] T003 Add `get_graph_counts()` method to `Neo4jGraphBackend` and use it in `build_graph()` / `append_documents()` return paths instead of `get_graph_data()`.
- [ ] T004 Add `normalized_aliases` index to `SCHEMA_QUERIES` in `neo4j_queries.py`.

**Checkpoint**: Schema checks run once, post-build returns counts without full graph load, alias index exists.

---

## Phase 2: Core Optimization — Entity Cache

**Purpose**: Eliminate N+1 entity lookup pattern.

- [ ] T005 Add bulk entity pre-load query `BULK_LOAD_ENTITIES_QUERY` to `neo4j_queries.py`.
- [ ] T006 Add `_bulk_load_entity_cache()` method to `Neo4jGraphBackend` that loads all entities for a graph_id into a dict keyed by `(entity_type, normalized_name)`.
- [ ] T007 Refactor `_persist_chunk()` to accept and use a shared `entity_cache` dict, checking cache before calling `_find_existing_entity()`.
- [ ] T008 Wire entity cache into `build_graph()` and `append_documents()` — pre-load before persistence loop, pass to `_persist_chunk()`.

**Checkpoint**: Entity lookups use in-memory cache; Neo4j round-trips for entity deduplication reduced to near-zero.

---

## Phase 3: Core Optimization — Batched Writes

**Purpose**: Reduce per-chunk Neo4j round-trips.

- [ ] T009 Add `BATCH_UPSERT_ENTITIES_QUERY` and `BATCH_UPSERT_RELATIONS_QUERY` to `neo4j_queries.py` using UNWIND.
- [ ] T010 Add `_persist_chunks_batched()` method to `Neo4jGraphBackend` that collects entities/relations across chunks and writes in batches.
- [ ] T011 Wire batched persistence into `build_graph()` and `append_documents()`.

**Checkpoint**: Persistence uses batched UNWIND writes; round-trips proportional to batch count, not entity count.

---

## Phase 4: Verification

- [ ] T012 Run existing unit tests in `tests/unit_test/mirofish_graph/` to verify no regressions.
- [ ] T013 Verify entity deduplication correctness is preserved — alias matching, preferred name selection, normalized_aliases merging.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** (T001-T004): No dependencies, all independent
- **Phase 2** (T005-T008): Depends on Phase 1 completion
- **Phase 3** (T009-T011): Depends on Phase 2 (entity cache must exist first)
- **Phase 4** (T012-T013): Depends on all implementation phases

### Parallel Opportunities

- T001, T002, T003, T004 are all independent — can be done in parallel
- T005 and T006 are independent of T001-T004
- T009 can start while T007-T008 are being completed
