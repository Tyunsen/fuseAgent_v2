# Tasks: Trace Graph Citations

**Input**: Design documents from `/specs/017-trace-graph-citations/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Verification is required because this increment changes time-mode graph quality, citation interaction, entity-mode graph fallback, and remote QA acceptance.

## Constitution Requirements

- This feature changes QA behavior, so final validation MUST re-run full `iw_docs` acceptance.
- The three trace modes remain valid only when the user explicitly `@知识库`.
- Time mode MUST render one readable gantt main graph.
- Entity mode MUST prefer a non-empty answer-scoped subgraph when a graph-ready collection is queried.
- Inline `[n]` citations MUST be clickable and MUST NOT appear as a detached header strip.
- Remote deployment plus fresh-message browser verification remain mandatory before sign-off.

## Phase 1: Setup

- [ ] T001 Review `specs/017-trace-graph-citations/spec.md`, `specs/017-trace-graph-citations/plan.md`, `specs/017-trace-graph-citations/research.md`, `specs/017-trace-graph-citations/data-model.md`, `specs/017-trace-graph-citations/contracts/trace-graph-display.md`, `specs/017-trace-graph-citations/contracts/citation-drawer-contract.md`, and `specs/017-trace-graph-citations/quickstart.md`.
- [ ] T002 Inspect the current chat citation shell, trace-support time label derivation, and entity graph fallback in `web/src/components/chat/message-parts-ai.tsx`, `web/src/components/chat/message-part-ai.tsx`, `web/src/components/chat/message-answer-support.tsx`, `web/src/components/chat/message-answer-graph.tsx`, `aperag/service/trace_support_service.py`, and `aperag/service/answer_graph_service.py`.

## Phase 2: Foundational

- [ ] T003 [P] Add shared helpers or state wiring for answer-body citation interaction in `web/src/components/chat/message-answer-support.types.ts`, `web/src/components/chat/message-parts-ai.tsx`, and `web/src/components/chat/message-part-ai.tsx`.
- [ ] T004 [P] Tighten shared trace-support payload shaping for readable titles and fallback graph selection in `aperag/service/trace_support_service.py` and `aperag/service/answer_graph_service.py`.

**Checkpoint**: Shared citation and trace-support foundations are ready for story work.

## Phase 3: User Story 1 - Time Gantt Must Be Readable And True (Priority: P1) MVP

**Goal**: Time mode renders a gantt main graph with real event labels and differentiated dates instead of collapsing everything into one day.

**Independent Test**: Ask `3月发生了什么？` in time mode against a graph-ready `@知识库`, then confirm the main graph is a gantt, task labels are real events, and multiple evidence-backed dates appear at multiple time positions.

### Tests for User Story 1

- [ ] T005 [P] [US1] Add time-title and time-label regression coverage in `tests/unit_test/answer_graph/test_trace_support_service.py`.
- [ ] T006 [P] [US1] Add time-mode prompt guidance regression coverage in `tests/unit_test/service/test_agent_chat_trace_mode.py`.

### Implementation for User Story 1

- [ ] T007 [US1] Improve conclusion title cleaning and time-label derivation in `aperag/service/trace_support_service.py`.
- [ ] T008 [US1] Keep time-mode prompt guidance aligned with gantt-only output in `aperag/service/trace_answer_service.py`.
- [ ] T009 [US1] Refine gantt label sanitization and time placement in `web/src/components/chat/message-answer-graph.tsx`.

**Checkpoint**: Time mode shows one readable gantt with evidence-backed labels and dates.

## Phase 4: User Story 2 - Inline Citations Must Be Clickable And Header Strip Removed (Priority: P1)

**Goal**: Cited prose shows clickable inline `[n]` markers and the header no longer renders a detached citation-number list.

**Independent Test**: On any cited answer, confirm the header has no `[1][2][3]` strip, the answer body contains clickable `[n]` markers, and clicking one opens and focuses the right-side `参考文档来源` drawer.

### Tests for User Story 2

- [ ] T010 [P] [US2] Add targeted citation interaction coverage in the nearest existing frontend test harness or runtime verification notes for `web/src/components/chat/`.

### Implementation for User Story 2

- [ ] T011 [US2] Remove the detached header citation strip in `web/src/components/chat/message-parts-ai.tsx`.
- [ ] T012 [US2] Render clickable inline citation anchors in `web/src/components/chat/message-part-ai.tsx` and `web/src/components/markdown.tsx` if needed.
- [ ] T013 [US2] Reuse the existing drawer state so inline citations open and focus the right-side drawer in `web/src/components/chat/message-parts-ai.tsx` and `web/src/components/chat/message-answer-support.tsx`.

**Checkpoint**: Citations are inline, clickable, and drawer-linked.

## Phase 5: User Story 3 - Entity Mode Must Produce A Real Subgraph (Priority: P1)

**Goal**: Entity mode produces a non-empty answer-scoped knowledge subgraph for graph-ready `@知识库` queries when related graph elements exist.

**Independent Test**: Ask `说一下现在各方的诉求利益` in entity mode against a graph-ready `@知识库`, then confirm the main graph is a knowledge-graph subgraph rather than an empty fallback card.

### Tests for User Story 3

- [ ] T014 [P] [US3] Add entity fallback regression coverage in `tests/unit_test/answer_graph/test_answer_graph_service.py` and/or `tests/unit_test/answer_graph/test_trace_support_service.py`.

### Implementation for User Story 3

- [ ] T015 [US3] Improve answer-scoped graph matching and fallback widening in `aperag/service/answer_graph_service.py`.
- [ ] T016 [US3] Improve trace-support focus-entity selection and row binding for entity mode in `aperag/service/trace_support_service.py`.
- [ ] T017 [US3] Confirm entity mode reuses the knowledge-graph renderer in `web/src/components/chat/message-answer-graph.tsx`.

**Checkpoint**: Entity mode produces a non-empty answer-scoped knowledge subgraph when relevant graph elements exist.

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T018 Run targeted backend verification for `tests/unit_test/service/test_agent_chat_trace_mode.py`, `tests/unit_test/answer_graph/test_trace_support_service.py`, and `tests/unit_test/answer_graph/test_answer_graph_service.py`.
- [ ] T019 [P] Run `corepack yarn lint` in `web/`.
- [ ] T020 [P] Run `corepack yarn build` in `web/` and regenerate `web/build/`.
- [ ] T021 Sync changed backend/frontend files and `web/build/` to `/home/common/jyzhu/ucml/fuseAgent-current`.
- [ ] T022 Restart the remote stack, restore local forwarding, and verify fresh messages against `http://127.0.0.1:46130/`.
- [ ] T023 Import the full acceptance dataset from `E:\codes\fuseAgent_v2\iw_docs` into a fresh remote knowledge base.
- [ ] T024 Verify vector, fulltext, and graph indexes complete within the 4-minute constitution budget.
- [ ] T025 Verify the collection graph page renders and satisfies node count > 80 and edge count > 100.
- [ ] T026 Verify fresh-message default, time, space, and entity mode behavior matches the constitution contracts.
- [ ] T027 Re-run `python scripts/run_triple_trace_acceptance.py --skip-remote-deploy` and continue the fix/redeploy/reverify loop until it passes.

## Dependencies & Execution Order

- Setup and Foundational phases come first.
- US1 and US2 can proceed after Foundational; they touch different layers but must merge cleanly before final browser verification.
- US3 depends on the shared fallback groundwork from Phase 2 and should land before remote acceptance.
- Polish depends on all selected user stories being complete.

## Parallel Opportunities

- T003 and T004 can run in parallel.
- T005 and T006 can run in parallel.
- T010 and T014 can run in parallel if the test harness split is clean.
- T019 and T020 can run in parallel after implementation stabilizes.

## Notes

- This repository has a dirty worktree. Do not revert unrelated edits.
- Remote frontend deployment must include regenerated `web/build/`.
- Final QA proof must come from fresh answers after deployment, not from historical messages only.
- Constitution-tagged strict acceptance items are not optional. If they fail, the implementation is not complete and the execution loop must continue.
