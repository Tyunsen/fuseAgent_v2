# Implementation Plan: MiroFish Build Speed Recovery

**Branch**: `014-mirofish-build-speed` | **Date**: 2026-04-03 | **Spec**: [spec.md](E:/codes/fuseAgent_v2/fuseAgent/specs/014-mirofish-build-speed/spec.md)  
**Input**: Feature specification from [spec.md](E:/codes/fuseAgent_v2/fuseAgent/specs/014-mirofish-build-speed/spec.md)

## Summary

Recover MiroFish graph build throughput so the recurring acceptance dataset under
`E:\codes\fuseAgent_v2\iw_docs` can finish vector, fulltext, and graph indexing
within 4 minutes on the remote acceptance environment while preserving the accepted
graph workbench UI baseline and the default/time/space/entity answer contracts.

## Technical Context

**Language/Version**: Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend  
**Primary Dependencies**: FastAPI, Celery, SQLAlchemy-backed services, existing document lifecycle services, existing MiroFish graph pipeline, Neo4j driver, Next.js 15, next-intl, Mermaid, existing e2e helpers  
**Storage**: PostgreSQL metadata, object storage for uploaded/parsed documents, Elasticsearch fulltext index, vector store, Neo4j-backed MiroFish graph data  
**Testing**: Targeted `pytest`, `corepack yarn lint`, `corepack yarn build`, remote service restart, local port-forward smoke validation, recurring acceptance script execution  
**Target Platform**: Linux-hosted remote deployment via Docker Compose, validated from Windows development environment through local forwarded ports  
**Project Type**: Full-stack web application with recurring acceptance automation  
**Performance Goals**: Full `iw_docs` import reaches vector/fulltext/graph ready within 4 minutes; collection graph page renders >80 nodes and >100 edges; accepted answer-mode contracts remain intact  
**Constraints**: Keep default mode unchanged, preserve accepted UI baseline from `ui-satisfied-graph-workbench`, no system-wide intent layer, no event/fact-unit model, no branch pollution of the approved UI baseline, remote runtime remains the source of truth  
**Scale/Scope**: Recurring acceptance import path, graph build throughput, graph payload/schema stability, answer-support graph usability, and automation needed to prove the speed recovery

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Acceptance plan identifies that this feature MUST import all documents from `E:\codes\fuseAgent_v2\iw_docs` and verify a 4-minute full-index completion budget.
- [x] Validation plan states the required graph quality thresholds: rendered collection graph, node count > 80, edge count > 100.
- [x] The QA mode plan preserves the required output contract for default, time, entity, and space trace behavior, including the fixed-location focus plus location-specific gantt requirement.
- [x] UI behavior changes are limited to preserving or reusing the approved baseline from `ui-satisfied-graph-workbench`; no new UI branch pollution is allowed.
- [x] Post-implement validation names the remote startup path, local port-forward targets, and automated acceptance path used for final sign-off.
- [x] The plan stays inside the approved increment: speed recovery plus non-regression of graph/workbench and answer-mode contracts.

## Phase 0 Research

See [research.md](E:/codes/fuseAgent_v2/fuseAgent/specs/014-mirofish-build-speed/research.md). The key conclusions are:

1. The recurring acceptance bottleneck is not one single failure but a chain: unsupported import file types, two-step upload/confirm overhead, over-large ontology payloads, graph-ready schema mismatches, and graph chunk counts large enough to exceed the 4-minute budget.
2. The highest-leverage runtime optimization is to reduce graph extraction work per acceptance build by capping chunk count through adaptive chunk sizing rather than only increasing concurrency.
3. The recurring acceptance script should use the fastest product-supported import path, normalize unsupported file formats before upload, and always emit a structured failure report instead of aborting without evidence.
4. Graph-ready state alone is insufficient; answer-support must successfully consume graph data without payload validation failures.
5. The accepted graph workbench UI remains the baseline; speed work should not redesign it.

## Phase 1 Design

### Data Model

See [data-model.md](E:/codes/fuseAgent_v2/fuseAgent/specs/014-mirofish-build-speed/data-model.md). The increment centers on:

- Acceptance run
- Acceptance collection
- Acceptance import source
- Graph build profile
- Graph-ready payload
- Mode contract result
- Acceptance report

### Interface Contracts

See [acceptance-report.md](E:/codes/fuseAgent_v2/fuseAgent/specs/014-mirofish-build-speed/contracts/acceptance-report.md).

### Quickstart

See [quickstart.md](E:/codes/fuseAgent_v2/fuseAgent/specs/014-mirofish-build-speed/quickstart.md) for the recurring acceptance flow.

## Project Structure

### Documentation (this feature)

```text
specs/014-mirofish-build-speed/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- acceptance-report.md
`-- tasks.md
```

### Source Code (repository root)

```text
aperag/
|-- mirofish_graph/
|   |-- graph_extractor.py
|   |-- llm_client.py
|   `-- neo4j_graph_backend.py
|-- service/
|   |-- document_service.py
|   |-- mirofish_graph_service.py
|   `-- trace_answer_service.py
`-- views/
    |-- auth.py
    `-- test.py

scripts/
|-- deploy-fuseagent-remote.sh
|-- run_triple_trace_acceptance.py
`-- tunnel_remote_fuseagent.py

tests/
|-- e2e_test/
|   |-- conftest.py
|   `-- test_chat.py
`-- unit_test/
    `-- mirofish_graph/
        `-- test_mirofish_graph_service.py

web/
|-- build/
`-- src/
    `-- app/
        `-- workspace/
            `-- collections/
                |-- graph/
                `-- documents/
```

**Structure Decision**: Keep the current backend/frontend layout, optimize the
existing MiroFish and document lifecycle paths in place, and add one recurring
acceptance script under `scripts/` instead of inventing a new performance-only subsystem.

## Implementation Strategy

### Phase 1: Recurring Acceptance Automation Stabilization

- Upgrade `scripts/run_triple_trace_acceptance.py` so it can execute repeatedly against the remote environment without manual intervention.
- Normalize unsupported dataset formats during acceptance import without dropping their content from the accepted knowledge base.
- Prefer the fastest supported import path and add robust retry/reporting behavior so failures surface as structured evidence instead of silent crashes.

### Phase 2: Graph Build Throughput Recovery

- Reduce MiroFish graph build work per acceptance run by introducing adaptive graph chunk sizing and related guardrails in `neo4j_graph_backend.py` and supporting services.
- Keep graph extraction broad enough to preserve the >80 node / >100 edge thresholds while reducing the total extraction task count.
- Reuse the current MiroFish path instead of adding a second graph pipeline.

### Phase 3: Graph Payload And Answer-Support Reliability

- Ensure graph-ready payloads returned from MiroFish can always pass the answer-support schema and no longer trigger false graph-unavailable fallbacks.
- Preserve default/time/space/entity answer-mode contracts while allowing the acceptance script to validate them automatically.

### Phase 4: Remote Validation And Non-Regression

- Restart the real remote stack, forward ports locally, and run the recurring acceptance script against the forwarded URLs.
- Confirm the accepted graph workbench UI remains aligned with the `ui-satisfied-graph-workbench` baseline.
- Record remaining performance or contract gaps only if they are still reproducible after the optimization pass.

## Post-Design Constitution Check

- [x] The plan is tied to the recurring `iw_docs` acceptance dataset and 4-minute full-index budget.
- [x] Graph-quality thresholds (>80 nodes, >100 edges) are explicit and are part of sign-off.
- [x] Default/time/space/entity answer-mode contracts remain explicit and are treated as non-regression gates.
- [x] Remote startup, port-forwarding, and automated acceptance remain mandatory.
- [x] UI work is baseline-preserving only and stays isolated from the approved `ui-satisfied-graph-workbench` branch.

## Complexity Tracking

No constitution violations require justification for this increment.
