# Tasks: MiroFish Build Speed Recovery

**Input**: Design documents from `/specs/014-mirofish-build-speed/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Verification is required because this increment changes recurring acceptance automation, MiroFish graph throughput, and non-regression guarantees for accepted graph and QA behavior.

## Constitution Requirements

- Every completed implementation pass must be revalidated against the full `iw_docs` dataset.
- Remote runtime and local port-forward validation are mandatory.
- The accepted graph workbench UI baseline from `ui-satisfied-graph-workbench` must not be polluted.

## Phase 1: Setup

- [x] T001 Review `specs/014-mirofish-build-speed/spec.md`, `specs/014-mirofish-build-speed/plan.md`, `specs/014-mirofish-build-speed/research.md`, `specs/014-mirofish-build-speed/data-model.md`, `specs/014-mirofish-build-speed/contracts/acceptance-report.md`, and `specs/014-mirofish-build-speed/quickstart.md`.
- [x] T002 Identify the current acceptance bottlenecks from `scripts/run_triple_trace_acceptance.py`, `aperag/service/document_service.py`, `aperag/service/mirofish_graph_service.py`, and `aperag/mirofish_graph/neo4j_graph_backend.py`.
- [x] T003 If UI changes are needed, branch or isolate work from the approved baseline `ui-satisfied-graph-workbench` without modifying that baseline branch directly.

## Phase 2: Foundational

- [x] T004 [P] Add or update recurring acceptance fixtures/helpers in `tests/e2e_test/conftest.py` or `tests/e2e_test/` support modules.
- [x] T005 [P] Harden structured acceptance reporting in `scripts/run_triple_trace_acceptance.py`.
- [x] T006 Add or update any shared graph-ready payload normalization needed by `aperag/service/mirofish_graph_service.py` and related helpers.

## Phase 3: User Story 1 - Full Knowledge Base Ready Within Budget (Priority: P1)

**Goal**: Make the recurring `iw_docs` acceptance knowledge base finish vector/fulltext/graph indexing within 4 minutes.

**Independent Test**: Run `python scripts/run_triple_trace_acceptance.py` and confirm the full acceptance collection reaches graph ready within budget.

### Tests for User Story 1

- [x] T007 [P] [US1] Add or extend recurring acceptance automation coverage around import normalization and structured failure reporting in `scripts/run_triple_trace_acceptance.py` and supporting tests if practical.

### Implementation for User Story 1

- [x] T008 [US1] Optimize the acceptance import path in `scripts/run_triple_trace_acceptance.py` so unsupported accepted files are normalized without being skipped and upload overhead is minimized.
- [x] T009 [US1] Optimize graph build throughput in `aperag/mirofish_graph/neo4j_graph_backend.py` and `aperag/service/mirofish_graph_service.py`, focusing on chunk-count reduction and build efficiency.
- [x] T010 [US1] Keep the remote environment configuration aligned with graph-ready execution in `docker-compose.deploy.remote.yml`, `envs/docker.env.overrides`, and `envs/env.remote.template` where needed.

## Phase 4: User Story 2 - Graph Workbench Stays Correct (Priority: P1)

**Goal**: Preserve graph workbench correctness and graph density after the speed optimization.

**Independent Test**: Open the acceptance collection graph page and confirm successful rendering with >80 nodes and >100 edges.

### Tests for User Story 2

- [x] T011 [P] [US2] Extend graph payload normalization coverage in `tests/unit_test/mirofish_graph/test_mirofish_graph_service.py` and `tests/unit_test/answer_graph/test_answer_graph_service.py`.

### Implementation for User Story 2

- [x] T012 [US2] Fix any graph-ready payload/schema mismatch in `aperag/service/mirofish_graph_service.py` and related graph-mapping helpers.
- [x] T013 [US2] Preserve the approved graph workbench baseline in `web/src/app/workspace/collections/[collectionId]/graph/` and related shared graph components, only if required by non-regression fixes.

## Phase 5: User Story 3 - Answer Modes Keep Their Contracts (Priority: P2)

**Goal**: Ensure default/time/space/entity modes still satisfy the constitution after speed recovery.

**Independent Test**: Run the recurring acceptance script and confirm all four mode validations pass.

### Tests for User Story 3

- [x] T014 [P] [US3] Extend answer-mode regression checks in `tests/unit_test/service/test_agent_chat_trace_mode.py`, `tests/unit_test/answer_graph/test_trace_support_service.py`, and `tests/unit_test/answer_graph/test_answer_graph_service.py`.

### Implementation for User Story 3

- [x] T015 [US3] Ensure mode-specific answer guidance remains aligned with the constitution in `aperag/service/trace_answer_service.py`.
- [x] T016 [US3] Ensure answer-support graph rendering supports the required gantt/subgraph contracts in `web/src/components/chat/message-answer-graph.tsx` and `web/src/components/chat/message-answer-support.tsx`.
- [x] T017 [US3] Ensure recurring acceptance mode validation in `scripts/run_triple_trace_acceptance.py` checks the required default/time/space/entity artifacts.

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T018 Run targeted backend verification for recurring acceptance, graph throughput, graph payload normalization, and answer-mode regressions.
- [x] T019 [P] Run `corepack yarn lint` in `web/`.
- [x] T020 [P] Run `corepack yarn build` in `web/` and refresh `web/build/`.
- [x] T021 Restart the latest applicable remote stack, forward ports locally, run `python scripts/run_triple_trace_acceptance.py`, and record the acceptance report results in the feature notes.

## Dependencies & Execution Order

- Setup tasks first.
- Foundational tasks block user story work.
- US1 must complete before final acceptance because the current blocker is the 4-minute budget.
- US2 and US3 depend on US1 stabilizing because they validate non-regression on the optimized build path.

## Notes

- This feature is successful only when the recurring acceptance report passes, not merely when local tests pass.
- Preserve the approved `ui-satisfied-graph-workbench` baseline if any graph/workbench UI files need touching.
