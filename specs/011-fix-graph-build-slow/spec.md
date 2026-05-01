# Feature Specification: MiroFish Graph Build Performance Optimization

**Feature Branch**: `011-fix-graph-build-slow`  
**Created**: 2026-04-02  
**Status**: Draft  
**Input**: User description: "不懂为什么，图索引构建就是很慢，我记得mirofish就是很快的啊，你严查一下为什么，并修复。之前尝试过修复，但是没成功，你好好弄"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Graph Build Completes in Reasonable Time for Typical Document Sets (Priority: P1)

As a knowledge-base maintainer, I want the graph index to build quickly (comparable to vector/fulltext indexing in perceived responsiveness), so I don't have to wait an excessively long time after confirming documents.

**Why this priority**: This is the user's core complaint. Graph build feels much slower than it should. The previous fix (removing the 10-second Celery countdown delay) was superficial and did not address the actual processing bottlenecks.

**Independent Test**: Upload a multi-document knowledge base and compare graph build times before and after the fix. The primary metric is total wall-clock time from task start to completion.

**Acceptance Scenarios**:

1. **Given** a collection with 10 documents producing ~100 text chunks, **When** graph indexing is triggered, **Then** the Neo4j persistence phase completes at least 3x faster than before the optimization (measured separately from LLM extraction time).
2. **Given** a collection that previously took observable minutes for graph persistence, **When** graph indexing completes, **Then** the persistence phase is no longer the dominant bottleneck (LLM extraction should be the time-limiting factor, not Neo4j writes).

---

### User Story 2 - Large Graph Builds Do Not Degrade Disproportionately (Priority: P1)

As a knowledge-base maintainer working with larger document sets, I want graph indexing performance to scale reasonably with document count, so adding more documents does not cause the build time to grow exponentially.

**Why this priority**: The N+1 entity lookup pattern causes quadratic degradation as the graph accumulates more entities. Each new entity must scan existing entities one-by-one.

**Independent Test**: Build a graph with 20+ documents and verify that persistence time grows linearly (not quadratically) with chunk count.

**Acceptance Scenarios**:

1. **Given** a graph build with N chunks, **When** persistence completes, **Then** the number of Neo4j round-trips is proportional to N (not N x entities-per-chunk).
2. **Given** graph entity count grows over successive builds, **When** entity deduplication lookups execute, **Then** lookup performance does not degrade as entity count increases.

---

### User Story 3 - Redundant Overhead is Eliminated (Priority: P2)

As a system operator, I want the graph build pipeline to avoid unnecessary work such as repeated schema checks and over-fetching data, so system resources are used efficiently.

**Why this priority**: Multiple redundant operations add up: schema queries on every method call, loading the entire graph into memory just to count nodes/edges.

**Independent Test**: Monitor Neo4j query count during a build and verify that schema queries run only once and post-build data fetching is minimal.

**Acceptance Scenarios**:

1. **Given** a graph build operation, **When** the build pipeline starts, **Then** schema/constraint creation queries execute at most once per build (not once per public method call).
2. **Given** a graph build completes, **When** the system returns build results, **Then** it returns only count statistics without loading all graph nodes and edges into application memory.

### Edge Cases

- What happens when entity alias deduplication finds multiple matches across chunks processed in the same batch?
- What happens when a Neo4j write batch partially fails — does the system handle partial persistence correctly?
- What happens when the graph already has thousands of entities from previous builds and new documents are appended?
- What happens when concurrent graph builds for different collections run simultaneously?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST batch Neo4j entity lookups to eliminate the N+1 query pattern where each entity in each chunk triggers a separate `FIND_ENTITY_BY_ALIASES_QUERY` round-trip.
- **FR-002**: The system MUST batch chunk persistence writes so that multiple chunks' entities and relations are written in fewer Neo4j round-trips instead of one query per entity per chunk.
- **FR-003**: The system MUST cache the Neo4j schema readiness check so that `ensure_ready()` schema queries execute at most once per process or build operation, not on every public method call.
- **FR-004**: The system MUST replace the post-build `get_graph_data()` full graph load with a lightweight count query that returns only `node_count`, `edge_count`, and `chunk_count` without loading all nodes/edges/chunks into memory.
- **FR-005**: The system MUST maintain the existing entity deduplication behavior (alias matching, name normalization) — the optimization must produce the same graph output as the current sequential approach.
- **FR-006**: The system MUST preserve the existing incremental append behavior (`append_documents`) and transaction safety.
- **FR-007**: The system SHOULD add a Neo4j index on `normalized_aliases` to prevent full array scans during entity alias matching as the graph grows.

### Key Entities

- **Chunk Persistence Batch**: A group of extracted chunks whose entities and relations are written to Neo4j in a single batched operation instead of one-by-one.
- **Entity Lookup Cache**: An in-memory map of known entities built during a build session to avoid repeated Neo4j lookups for previously seen entities within the same build.
- **Schema Readiness Flag**: A per-process flag indicating that Neo4j schema constraints and indexes have already been verified, avoiding redundant checks.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a typical 10-document collection (~100 chunks), the total graph build time is reduced by at least 50% compared to the pre-optimization baseline.
- **SC-002**: Neo4j round-trips during persistence are reduced from O(chunks x entities-per-chunk) to O(chunks) or better.
- **SC-003**: Schema readiness queries execute at most once per build operation instead of once per public method call (reducing 7+ redundant round-trips per call to zero).
- **SC-004**: Post-build result collection uses a count-only query instead of loading the entire graph, reducing memory usage and query time for large graphs.

## Assumptions

- The LLM extraction phase (parallel via ThreadPoolExecutor with concurrency=32) is already reasonably optimized and is expected to remain the time-limiting factor for large builds after persistence is optimized.
- The existing `entity_lookup_idx` composite index on `(graph_id, entity_type, normalized_name)` is effective for exact-match lookups but insufficient for alias array scans.
- The previous fix attempt (removing the 10-second Celery countdown delay in `document_service.py`) was correct but insufficient — it addressed only queue scheduling latency, not the actual graph processing bottlenecks.
- Neo4j supports batch UNWIND operations that can replace individual MERGE queries for significantly better write throughput.
- Entity deduplication correctness (alias matching, preferred name selection) must be preserved exactly — this is a performance optimization, not a behavior change.
