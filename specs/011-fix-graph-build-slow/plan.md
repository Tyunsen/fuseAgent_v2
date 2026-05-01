# Implementation Plan: MiroFish Graph Build Performance Optimization

**Branch**: `011-fix-graph-build-slow` | **Date**: 2026-04-02 | **Spec**: `specs/011-fix-graph-build-slow/spec.md`
**Input**: Feature specification from `specs/011-fix-graph-build-slow/spec.md`

## Summary

Optimize MiroFish graph build performance by eliminating N+1 Neo4j query patterns,
batching persistence writes, caching schema readiness checks, replacing post-build
full graph loads with count-only queries, and adding missing database indexes. The
previous fix (removing a 10-second Celery countdown delay) was insufficient — the
actual bottlenecks are in the Neo4j persistence layer.

## Technical Context

**Language/Version**: Python 3.11.12
**Primary Dependencies**: Neo4j Python driver, ThreadPoolExecutor for LLM extraction, Celery task flow
**Storage**: Neo4j graph database for entity/relation/chunk storage
**Testing**: `pytest` unit tests in `tests/unit_test/mirofish_graph/`
**Target Platform**: Linux server deployment + local Windows development
**Project Type**: Backend graph indexing pipeline
**Performance Goals**: 50%+ reduction in graph build time; O(chunks) Neo4j round-trips instead of O(chunks × entities)
**Constraints**: Must preserve entity deduplication correctness (alias matching, name normalization); no changes to graph extraction prompts or LLM calls
**Scale/Scope**: Neo4j persistence layer only; LLM extraction concurrency is already optimized at 32 workers

## Phase 0 Research

Root cause analysis identified 5 bottlenecks (ordered by severity):

1. **N+1 Entity Lookups** (`neo4j_graph_backend.py:449-480`): Every entity in every chunk
   triggers a separate `FIND_ENTITY_BY_ALIASES_QUERY`. For 50 chunks × 8 entities = 400
   individual Neo4j round-trips just for lookups.

2. **Sequential Chunk Persistence** (`neo4j_graph_backend.py:103-115`): LLM extraction runs
   in parallel (ThreadPoolExecutor), but all Neo4j writes are sequential — one chunk at a
   time in a for loop.

3. **Redundant `ensure_ready()`** (`neo4j_client.py:64-72`): 7 schema queries (1 connectivity
   check + 4 constraints + 2 indexes) run on every public method call, not just once.

4. **Over-fetching `get_graph_data()`** (`neo4j_graph_backend.py:334-402`): After build/append,
   loads ALL nodes, edges, and chunks into memory just to return 3 count values.

5. **Missing `normalized_aliases` Index** (`neo4j_queries.py:91-100`): The alias fallback scan
   in `FIND_ENTITY_BY_ALIASES_QUERY` has no index, causing full array scans that degrade with
   graph size.

## Phase 1 Design

### Optimization 1: Cross-Chunk Entity Cache

Replace per-entity Neo4j lookups with a build-session entity cache:
- Before persistence begins, bulk-load all existing entities for the graph_id into an in-memory dict
- During chunk persistence, check the cache first (O(1) dict lookup) before hitting Neo4j
- After upserting a new entity, add it to the cache
- This eliminates the N+1 pattern entirely for entities already seen in earlier chunks

### Optimization 2: Batched Neo4j Writes

Replace individual `session.run()` calls per entity/relation with UNWIND-based batch queries:
- Collect all entities from a chunk (or multiple chunks) into a list
- Execute a single `UNWIND $batch AS item MERGE ...` query per batch
- Same for relations and chunks
- This reduces Neo4j round-trips from O(entities + relations) per chunk to O(1) per chunk

### Optimization 3: Schema Readiness Caching

Add a class-level `_schema_ready` flag to `Neo4jClientManager`:
- Set to `True` after first successful `ensure_ready()` call
- Skip schema queries on subsequent calls (just verify connectivity)
- Reset on `close()` for safety

### Optimization 4: Count-Only Post-Build Query

Add a `GRAPH_COUNTS_QUERY` that uses `count()` aggregation:
- Replace `get_graph_data()` calls at the end of `build_graph()` and `append_documents()`
  with a new `get_graph_counts()` method
- Keep `get_graph_data()` unchanged for API endpoints that need full data

### Optimization 5: Normalized Aliases Index

Add a fulltext or composite index on `Entity.normalized_aliases` to speed up the
alias fallback scan in `FIND_ENTITY_BY_ALIASES_QUERY`.

## Project Structure

### Source Code Changes

```text
aperag/mirofish_graph/
├── neo4j_client.py          # Add schema readiness caching
├── neo4j_queries.py         # Add GRAPH_COUNTS_QUERY, BATCH_UPSERT queries, alias index
└── neo4j_graph_backend.py   # Entity cache, batched writes, count-only post-build

tests/unit_test/mirofish_graph/
└── test_mirofish_graph_service.py  # Verify existing tests still pass
```

## Implementation Strategy

### Step 1: Low-Risk Quick Wins (Independent)
- Cache `ensure_ready()` schema checks
- Add count-only `GRAPH_COUNTS_QUERY` and `get_graph_counts()` method
- Add `normalized_aliases` index to `SCHEMA_QUERIES`

### Step 2: Core Optimization (Sequential)
- Build cross-chunk entity cache with bulk pre-load
- Refactor `_persist_chunk()` to use entity cache instead of per-entity lookups
- Convert entity and relation writes to batched UNWIND queries

### Step 3: Integration (Sequential)
- Wire optimizations into `build_graph()` and `append_documents()`
- Run existing tests to verify correctness

## Post-Design Constitution Check

- [x] Changes are limited to the Neo4j persistence layer
- [x] Entity deduplication behavior (alias matching, name normalization) is preserved
- [x] No UI changes
- [x] No changes to LLM extraction or graph extraction prompts
