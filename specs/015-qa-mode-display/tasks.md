# Tasks: QA Mode Display

**Input**: Design documents from `/specs/015-qa-mode-display/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Verification is required because this increment changes visible QA behavior, graph rendering mode selection, reference presentation, and MiroFish document status refresh behavior.

## Constitution Requirements

- This feature changes QA behavior and graph-related UI, so final validation MUST re-run full `iw_docs` acceptance.
- Space mode MUST stay shell-compatible with default mode and use `graph TD`.
- Entity mode MUST reuse the existing knowledge-graph renderer rather than Mermaid.
- UI work must remain isolated from the approved `ui-satisfied-graph-workbench` baseline branch.
- Remote verification and local port-forward access are mandatory before calling the feature complete.

## Phase 1: Setup

- [x] T001 Review `specs/015-qa-mode-display/spec.md`, `specs/015-qa-mode-display/plan.md`, `specs/015-qa-mode-display/research.md`, `specs/015-qa-mode-display/data-model.md`, `specs/015-qa-mode-display/contracts/chat-answer-display.md`, `specs/015-qa-mode-display/contracts/document-graph-status-refresh.md`, and `specs/015-qa-mode-display/quickstart.md`.
- [x] T002 Identify reusable answer-shell, graph, citation, and document-page refresh code in `web/src/components/chat/`, `web/src/app/workspace/collections/[collectionId]/documents/`, `aperag/service/agent_chat_service.py`, and `aperag/service/trace_answer_service.py`.
- [x] T003 If additional UI work branches are needed, keep all work isolated from the approved `ui-satisfied-graph-workbench` baseline branch.

## Phase 2: Foundational

- [x] T004 [P] Add or update shared frontend trace display copy in `web/src/i18n/en-US.json` and `web/src/i18n/zh-CN/page_chat.json`.
- [x] T005 [P] Add or update shared chat support typing/helpers in `web/src/components/chat/message-answer-support.types.ts`.
- [x] T006 Add or update shared backend trace-mode answer guidance in `aperag/service/trace_answer_service.py`.

**Checkpoint**: Shared strings, trace-mode shell rules, and support types are ready for story work.

## Phase 3: User Story 1 - Streamed Answer With Unified Citations (Priority: P1)

**Goal**: Keep answer text streamed while all modes share one visible inline citation model plus one collapsed source list.

**Independent Test**: Ask a source-backed question in any mode and confirm answer text streams incrementally, inline citation markers remain visible, and only one collapsed 鈥滄湰娆″洖绛旀枃妗ｆ潵婧愨€?surface is shown.

### Tests for User Story 1

- [x] T007 [P] [US1] Add frontend regression coverage for unified source list and removed duplicate source surfaces in `web/src/components/chat/` tests or equivalent existing test location if present.
- [x] T008 [P] [US1] Add backend regression coverage for answer post-processing that strips duplicate standalone source sections in `tests/unit_test/service/` or the nearest existing test module.

### Implementation for User Story 1

- [x] T009 [US1] Keep streaming answer delivery on the existing path in `aperag/service/agent_chat_service.py` and any related stream format utilities it depends on.
- [x] T010 [US1] Remove duplicate standalone source-section prompting from `aperag/service/trace_answer_service.py` and any related prompt assembly path in `aperag/service/prompt_template_service.py` if needed.
- [x] T011 [US1] Update `web/src/components/chat/message-parts-ai.tsx` so the answer shell uses a single unified evidence entry point and no longer duplicates source surfaces.
- [x] T012 [US1] Update `web/src/components/chat/message-reference.tsx` and `web/src/components/chat/message-reference-card.tsx` so the 鈥滄湰娆″洖绛旀枃妗ｆ潵婧愨€?list is collapsed by default and remains expandable.
- [x] T013 [US1] Keep inline citation rendering compatible with the simplified answer shell in `web/src/components/chat/message-part-ai.tsx`.

**Checkpoint**: The answer shell stays streamed and source-backed without duplicate source cards.

## Phase 4: User Story 2 - Default, Time, And Space Modes Share The Minimal Shell (Priority: P1)

**Goal**: Remove summary/conclusion/source duplication from default, time, and space modes while preserving their intended primary graph type.

**Independent Test**: Ask the same question in default, time, and space modes and confirm there are no extra summary/conclusion/source cards; default and space use `graph TD`, time uses gantt.

### Tests for User Story 2

- [x] T014 [P] [US2] Add frontend regression coverage for mode-specific primary graph selection and removal of duplicate answer-support cards in `web/src/components/chat/` tests or equivalent existing test location if present.

### Implementation for User Story 2

- [x] T015 [US2] Remove summary and key-conclusion card rendering from `web/src/components/chat/message-answer-support.tsx`.
- [x] T016 [US2] Update `web/src/components/chat/message-answer-graph.tsx` so default mode keeps topology, time mode keeps gantt, and space mode reuses the default `graph TD` path instead of the old location gantt path.
- [x] T017 [US2] Update trace-mode answer guidance in `aperag/service/trace_answer_service.py` so space mode follows the new constitution rule and no longer requests a location-specific gantt.
- [x] T018 [US2] Align user-facing mode copy and labels in `web/src/i18n/en-US.json` and `web/src/i18n/zh-CN/page_chat.json` if any old space-trace wording remains.

**Checkpoint**: Default/time/space modes share the same minimal shell and only differ by the intended primary graph.

## Phase 5: User Story 3 - Entity Mode Uses Knowledge Graph Rendering (Priority: P2)

**Goal**: Render the entity-mode main graph as a true knowledge-graph subgraph using the existing graph renderer, not Mermaid.

**Independent Test**: Ask an entity-mode question and confirm the main graph is rendered with the existing knowledge-graph visual style and only shows answer-relevant entities and edges.

### Tests for User Story 3

- [x] T019 [P] [US3] Add frontend regression coverage for entity-mode graph renderer selection in `web/src/components/chat/` tests or equivalent existing test location if present.

### Implementation for User Story 3

- [x] T020 [US3] Update `web/src/components/chat/message-answer-graph.tsx` so entity mode routes to the force-graph / knowledge-graph renderer as the primary visualization rather than Mermaid.
- [x] T021 [US3] Remove any extra entity-mode 鈥淜nowledge Graph 鍥炵瓟鍏宠仈鍥捐氨鈥?card path from `web/src/components/chat/message-answer-support.tsx`.
- [x] T022 [US3] Update backend trace-mode answer guidance in `aperag/service/trace_answer_service.py` so entity mode no longer instructs the model to emit Mermaid knowledge subgraphs.

**Checkpoint**: Entity mode uses the existing graph renderer and no longer duplicates graph surfaces.

## Phase 6: User Story 4 - Document Graph Status Visibility And 15-Second Refresh (Priority: P2)

**Goal**: Keep graph status visible per document and auto-refresh the documents page every 15 seconds only while the collection graph is actively building.

**Independent Test**: Open a MiroFish collection documents page during graph build and confirm the graph column is visible for each document, the page refreshes every 15 seconds, and stops refreshing after build completion.

### Tests for User Story 4

- [x] T023 [P] [US4] Add frontend regression coverage for MiroFish graph status visibility and refresh gating in the documents page components or nearest existing frontend test location.

### Implementation for User Story 4

- [x] T024 [US4] Keep the graph status column visible for MiroFish collections in `web/src/app/workspace/collections/[collectionId]/documents/documents-table.tsx` and `document-index-status.tsx`.
- [x] T025 [US4] Replace the collection-only explanatory copy in `web/src/app/workspace/collections/[collectionId]/documents/collection-index-overview.tsx` with wording that preserves document-level status visibility.
- [x] T026 [US4] Introduce client-side 15-second polling during active graph build in `web/src/app/workspace/collections/[collectionId]/documents/page.tsx` or an extracted client wrapper component that page uses.
- [x] T027 [US4] Preserve search params, pagination, sorting, and row expansion state across auto-refresh in `web/src/app/workspace/collections/[collectionId]/documents/documents-table.tsx` and related page wiring.

**Checkpoint**: The documents page exposes visible graph status per row and only polls during active build.

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T028 Run targeted backend verification for `aperag/service/agent_chat_service.py`, `aperag/service/trace_answer_service.py`, and any touched backend tests.
- [x] T029 [P] Run `python -m compileall aperag/service/agent_chat_service.py aperag/service/trace_answer_service.py scripts/run_triple_trace_acceptance.py`.
- [x] T030 [P] Run `corepack yarn lint` in `web/`.
- [x] T031 [P] Run `corepack yarn build` in `web/` and refresh `web/build/`.
- [x] T032 Import the full acceptance dataset from `E:\codes\fuseAgent_v2\iw_docs` into a fresh knowledge base and verify all required indexes finish within the constitution time budget.
- [x] T033 Verify the collection graph page renders successfully and satisfies the required node/edge thresholds.
- [x] T034 Verify default mode passes the current output contract: streamed answer text, inline citations, one collapsed source list, no duplicate summary/conclusion/source cards, and topology graph.
- [x] T035 Verify time mode passes the current output contract: same minimal shell as default mode, gantt primary graph, unified sources, no duplicate summary/conclusion/source cards.
- [x] T036 Verify space mode passes the current constitution contract: same minimal shell as default mode, `graph TD` primary graph, unified sources, no duplicate summary/conclusion/source cards.
- [x] T037 Verify entity mode passes the current output contract: knowledge-graph renderer as primary graph, answer-relevant subgraph only, unified sources, no duplicate summary/conclusion/source cards or extra graph card.
- [x] T038 Verify the MiroFish documents page shows graph status per document and only auto-refreshes every 15 seconds while the graph is building/updating.
- [x] T039 Restart the latest applicable remote service stack, forward ports locally, and automate final sign-off against the forwarded frontend/API URLs.

## Dependencies & Execution Order

- Setup first.
- Foundational tasks block all user stories.
- US1 and US2 can proceed in parallel after the foundational phase.
- US3 depends on US1 and US2 because it reuses the simplified answer shell and updated mode graph selection logic.
- US4 depends on foundational work only and can run in parallel with US3 once document-page implementation starts.
- Final acceptance depends on all user stories being complete.

## Parallel Opportunities

- T004 and T005 can run together.
- T007 and T008 can run together.
- T014 and T019 and T023 can run together if frontend test coverage is split cleanly.
- T030 and T031 can run in parallel after code changes settle.

## Notes

- This feature refines an already-dirty worktree; implementation must avoid reverting unrelated changes.
- Collection-level graph status remains the backend acceptance source of truth even though document-level status stays visible in the UI.
- Final sign-off still requires remote runtime validation and full constitution acceptance, not just local lint/build success.
- Frontend regression validation for this increment was completed through production-build browser smoke and forwarded-runtime checks because the repository does not provide a dedicated component-test harness for these chat and document surfaces.

