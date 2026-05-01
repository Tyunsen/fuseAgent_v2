# Tasks: Gantt Source Citations

**Input**: Design documents from `/specs/016-gantt-source-citations/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Verification is required because this increment changes time-mode graph quality, source access UI, and citation rendering in the answer body.

## Constitution Requirements

- This feature changes QA behavior and UI, so final validation MUST re-run full `iw_docs` acceptance.
- Time mode MUST render a single gantt main graph without extra secondary cards.
- UI work must remain isolated from the approved `ui-satisfied-graph-workbench` baseline branch.
- Remote verification and local forwarded URLs remain mandatory before sign-off.

## Phase 1: Setup

- [x] T001 Review `specs/016-gantt-source-citations/spec.md`, `specs/016-gantt-source-citations/plan.md`, `specs/016-gantt-source-citations/research.md`, `specs/016-gantt-source-citations/data-model.md`, `specs/016-gantt-source-citations/contracts/time-trace-display.md`, `specs/016-gantt-source-citations/contracts/answer-source-evidence.md`, and `specs/016-gantt-source-citations/quickstart.md`.
- [x] T002 Identify reusable time-trace, source-drawer, and citation code in `aperag/service/trace_answer_service.py`, `aperag/service/trace_support_service.py`, `web/src/components/chat/message-part-ai.tsx`, `web/src/components/chat/message-parts-ai.tsx`, and `web/src/components/chat/message-answer-support.tsx`.

## Phase 2: Foundational

- [x] T003 [P] Add or update shared prompt and display guards for raw Mermaid leakage in `aperag/service/trace_answer_service.py` and `web/src/components/chat/message-part-ai.tsx`.
- [x] T004 [P] Keep the shared answer-support graph path structured for time mode in `web/src/components/chat/message-answer-support.tsx` and `web/src/components/chat/message-answer-graph.tsx`.

**Checkpoint**: Shared time-mode flow and answer-body sanitization are ready for story work.

## Phase 3: User Story 1 - Time-Trace Main Graph Quality (Priority: P1) MVP

**Goal**: Time mode renders a true gantt with readable event labels and differentiated dates, with no secondary card below it.

**Independent Test**: Ask “3月发生了什么？” in time mode and confirm the main graph is a gantt, labels are real events, and the extra grouped card strip is gone.

### Tests for User Story 1

- [ ] T005 [P] [US1] Add targeted time-label/date-placement coverage in `tests/unit_test/answer_graph/test_trace_support_service.py`.
- [ ] T006 [P] [US1] Add time-mode prompt guidance regression coverage in `tests/unit_test/service/test_agent_chat_trace_mode.py`.

### Implementation for User Story 1

- [x] T007 [US1] Improve time conclusion title and time-label selection in `aperag/service/trace_support_service.py`.
- [x] T008 [US1] Ensure time-mode prompt guidance forbids `graph TD` fallback and generic numbered labels in `aperag/service/trace_answer_service.py`.
- [x] T009 [US1] Suppress the extra grouped-card section for time mode in `web/src/components/chat/message-answer-graph.tsx`.

**Checkpoint**: Time mode shows one gantt graph with real event labels and correct time separation.

## Phase 4: User Story 2 - Source Drawer In Action Bar (Priority: P1)

**Goal**: Move the source entry into the message action row and open sources from a right-side drawer.

**Independent Test**: On any cited answer, verify the action row contains `参考文档来源` and clicking it opens a right-side drawer while the old bottom source card is absent.

### Tests for User Story 2

- [ ] T010 [P] [US2] Add frontend regression coverage or runtime harness coverage notes for the action-row source entry and right-drawer behavior in the nearest existing chat UI test location.

### Implementation for User Story 2

- [x] T011 [US2] Move the source trigger into the message action row in `web/src/components/chat/message-parts-ai.tsx`.
- [x] T012 [US2] Replace the bottom collapsible source card with a controlled right-side drawer in `web/src/components/chat/message-answer-support.tsx`.
- [x] T013 [US2] Reuse the existing source row card inside the right drawer in `web/src/components/chat/message-reference-card.tsx`.

**Checkpoint**: Source access is message-scoped, action-bar-triggered, and drawer-based.

## Phase 5: User Story 3 - Inline Citation Numbering (Priority: P2)

**Goal**: Answer prose shows `[n]` citation markers that align with the source drawer numbering.

**Independent Test**: On any cited answer, verify the body contains visible `[n]` markers and the drawer rows use the same numbering.

### Tests for User Story 3

- [ ] T014 [P] [US3] Add targeted citation-numbering coverage in a chat UI test or nearest existing frontend verification file.

### Implementation for User Story 3

- [x] T015 [US3] Add stable answer-local citation numbering helpers in `web/src/components/chat/message-answer-support.types.ts` or a nearby chat helper module.
- [x] T016 [US3] Lift trace-support state or equivalent citation context so the message body can render inline `[n]` markers in `web/src/components/chat/message-parts-ai.tsx`.
- [x] T017 [US3] Apply inline citation marker rendering to visible answer prose in `web/src/components/chat/message-part-ai.tsx`.
- [x] T018 [US3] Align source drawer numbering with the same citation order in `web/src/components/chat/message-reference-card.tsx`.

**Checkpoint**: Body citations and drawer numbering stay consistent for cited answers.

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T019 Run targeted backend verification for `tests/unit_test/service/test_agent_chat_trace_mode.py` and `tests/unit_test/answer_graph/test_trace_support_service.py`.
- [x] T020 [P] Run `corepack yarn lint` in `web/`.
- [x] T021 [P] Run `corepack yarn build` in `web/` and regenerate `web/build/`.
- [x] T022 Sync changed backend/frontend files and `web/build/` to `/home/common/jyzhu/ucml/fuseAgent-current`.
- [x] T023 Restart the remote stack with `bash scripts/deploy-fuseagent-remote.sh`, restore local forwarding, and verify the new UI against `http://127.0.0.1:46130/`.
- [ ] T024 Re-run `python scripts/run_triple_trace_acceptance.py --skip-remote-deploy` and confirm the constitution budget plus graph thresholds still pass.

## Dependencies & Execution Order

- Setup and Foundational phases come first.
- US1 can proceed immediately after Foundational and should land before final acceptance.
- US2 can proceed in parallel with US1 because it mainly affects the message action bar and source drawer shell.
- US3 depends on US2 because citation numbering must align with the drawer numbering and source presentation.
- Polish depends on all selected user stories being complete.

## Parallel Opportunities

- T003 and T004 can run in parallel.
- T005 and T006 can run in parallel.
- T010 and T014 can run in parallel if a test harness is available.
- T020 and T021 can run in parallel after code changes settle.

## Notes

- This feature sits on top of an already-changing worktree; do not revert unrelated edits.
- Remote frontend deployment must refresh `web/build/` under the remote `web/` directory because the frontend image is built from the `web` Docker context.
- Runtime verification already confirms:
  - time mode no longer renders the extra grouped card below the gantt,
  - the source trigger sits in the message action row,
  - clicking the trigger opens a right-side drawer,
  - inline `[n]` citation markers are visible in the answer body.
