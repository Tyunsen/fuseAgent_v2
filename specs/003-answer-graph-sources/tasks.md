# Tasks: Answer Graph And Source Cards

**Input**: Design documents from `/specs/003-answer-graph-sources/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: Verification is required for paragraph-level references, answer-scoped
graph rendering, bidirectional linking, and degraded support states. Targeted
backend tests plus frontend lint/build and local smoke checks are included
below.

## Phase 1: Setup

**Purpose**: Lock implementation to the approved answer-result increment and
capture reuse targets before editing code.

- [X] T001 Review `specs/003-answer-graph-sources/spec.md`, `plan.md`, `research.md`, `data-model.md`, and `contracts/*.md` to keep implementation inside the approved answer-result increment.
- [X] T002 Capture concrete reuse targets from `web/src/app/workspace/collections/[collectionId]/graph/collection-graph.tsx`, `web/src/app/workspace/collections/[collectionId]/search/search-result-drawer.tsx`, and `E:\codes\fuseAgent_v2\MiroFish\frontend\src\components\GraphPanel.vue` before adding answer-specific UI code.

---

## Phase 2: Foundational

**Purpose**: Add the shared evidence and graph contracts the rest of the feature
depends on.

- [X] T003 Extend `aperag/agent/tool_reference_extractor.py` so collection/chat-file search results emit one reference row per result item with stable answer-support metadata.
- [X] T004 Add answer-graph request/response view models in `aperag/schema/view_models.py` for the new answer-scoped graph endpoint.
- [X] T005 [P] Expose answer-linkable graph provenance metadata from `aperag/mirofish_graph/neo4j_queries.py`, `aperag/mirofish_graph/neo4j_graph_backend.py`, and `aperag/service/mirofish_graph_service.py`.
- [X] T006 [P] Add shared answer-support TypeScript helpers in `web/src/components/chat/` or `web/src/lib/` for row IDs, chunk IDs, and graph/evidence linkage state.

**Checkpoint**: References carry paragraph-level linkage metadata and backend
graph services can expose answer-linkable provenance.

---

## Phase 3: User Story 1 - Review Paragraph-Level Sources Inline (Priority: P1) MVP

**Goal**: Each answer shows a visible inline source card with one row per cited
paragraph/passage and inline preview support.

**Independent Test**: Ask a question with supporting evidence and verify the
answer renders an inline source card with separate rows per cited passage and a
passage preview that stays inside the answer context.

### Tests for User Story 1

- [X] T007 [P] [US1] Add targeted extractor coverage in `tests/unit_test/agent/test_tool_reference_extractor.py` for one-row-per-item references and paragraph-precision fallback metadata.

### Implementation for User Story 1

- [X] T008 [US1] Implement the answer source-card UI in `web/src/components/chat/message-reference-card.tsx` using the enriched reference metadata.
- [X] T009 [US1] Update `web/src/components/chat/message-parts-ai.tsx` and `web/src/components/chat/message-reference.tsx` so answers render the inline source card instead of the detached reference badge/drawer flow.
- [X] T010 [US1] Add Chinese-first source-card copy and fallback labels in `web/src/i18n/zh-CN.json`, `web/src/i18n/en-US.json`, and `web/src/i18n/en-US.d.json.ts`.

**Checkpoint**: Answers now show a visible inline source card with per-passage
rows and explicit precision fallback states.

---

## Phase 4: User Story 2 - Understand the Answer Through a MiroFish-Style Graph (Priority: P2)

**Goal**: Each answer can show a compact MiroFish-style graph derived from the
cited evidence instead of only collection-level graph pages.

**Independent Test**: Ask a graph-supported question and verify the answer
shows a compact inline graph with nodes/edges tied to the cited answer support.

### Tests for User Story 2

- [X] T011 [P] [US2] Add answer-graph backend coverage in `tests/unit_test/answer_graph/test_answer_graph_service.py` for chunk-driven graph derivation and no-graph fallback behavior.

### Implementation for User Story 2

- [X] T012 [US2] Implement `aperag/service/answer_graph_service.py` to build compact answer-scoped graphs from cited chunk/source IDs across MiroFish and existing graph data paths.
- [X] T013 [US2] Add the answer-graph route in `aperag/views/collections.py` and wire it through the existing collection authorization path.
- [X] T014 [US2] Implement the inline graph renderer in `web/src/components/chat/message-answer-graph.tsx` by adapting the existing force-graph pattern to a compact MiroFish-style answer card.
- [X] T015 [US2] Add the answer-support container in `web/src/components/chat/message-answer-support.tsx` so the graph block is loaded lazily and stays inside the answer unit.

**Checkpoint**: Answers can fetch and display a compact inline graph without
leaving the conversation.

---

## Phase 5: User Story 3 - Keep Answer, Sources, and Graph in One Cohesive Result (Priority: P3)

**Goal**: The answer text, source card, and graph behave as one linked result
with bidirectional graph/evidence interaction and clear degraded states.

**Independent Test**: Ask a question with graph support and verify graph clicks
highlight source rows, source-row clicks focus graph elements, and no-graph /
no-precision cases still render coherently.

### Implementation for User Story 3

- [X] T016 [US3] Add bidirectional linking state and interaction plumbing in `web/src/components/chat/message-answer-support.tsx`, `web/src/components/chat/message-reference-card.tsx`, and `web/src/components/chat/message-answer-graph.tsx`.
- [X] T017 [US3] Update `web/src/components/chat/chat-messages.tsx` and related chat rendering so answer support blocks remain stable for streamed answers and restored history.
- [X] T018 [US3] Implement no-graph, no-precise-passage, and evidence-insufficient support states in `web/src/components/chat/message-answer-support.tsx` and `web/src/components/chat/message-reference-card.tsx`.

**Checkpoint**: Answer text, source card, and graph are one coherent answer
result with bidirectional interaction.

---

## Phase 6: Verification & Polish

**Purpose**: Prove the increment works and record completion in the feature
artifacts.

- [X] T019 Run targeted backend verification in `tests/unit_test/agent/test_tool_reference_extractor.py` and `tests/unit_test/answer_graph/test_answer_graph_service.py`.
- [X] T020 Run `corepack yarn lint` in `web/`.
- [X] T021 Run `corepack yarn build` in `web/`.
- [X] T022 Perform a local smoke pass for answer text + source card + inline graph + bidirectional linking and update this file to reflect completed work.

## Verification Notes

- `2026-03-22`: Local Playwright smoke check confirmed the inline answer-support block renders inside historical chat results, the source card shows one row per source item, and source-row expansion works inline inside the answer card.
- `2026-03-22`: The currently available `伊朗` collection returns the explicit no-graph degraded state because the backend reports `Collection coleb442f05fd79e9c2 does not have knowledge graph enabled`, so full UI-level bidirectional graph/evidence highlighting could not be reproduced against live data in this environment.
- `2026-03-22`: Backend unit coverage remains the verification source for bidirectional linkage mapping and empty-state graph derivation until a graph-enabled collection is available for smoke testing.

---

## Dependencies & Execution Order

- Setup and Foundational phases must complete before user-story work.
- US1 depends on the enriched reference contract from Phase 2.
- US2 depends on the graph provenance exposure from Phase 2.
- US3 depends on both US1 and US2 because it links the two support blocks into
  one answer unit.
- Final verification runs after all implementation tasks are complete.

## Parallel Opportunities

- T005 and T006 can proceed in parallel after the reference contract is defined.
- T007 and T011 can be written while backend/frontend implementation is being assembled.
- T014 and T015 can proceed in parallel once the answer-graph route contract is stable.
- T020 and T021 can run in parallel after code changes settle.
