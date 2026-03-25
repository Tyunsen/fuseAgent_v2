# Tasks: ApeRAG Answer Topology And Sources

**Input**: Design documents from `/specs/004-answer-topology-sources/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: Verification is required because this increment changes visible
answer behavior. Targeted backend verification plus frontend lint/build and
local smoke checks are included below.

## Constitution Requirements

- Tasks stay inside the approved answer topology and source presentation increment.
- Reuse/adaptation tasks come before net-new code.
- UI work is limited to ApeRAG-parity source drawer behavior and MiroFish-style topology rendering.
- No deployment tasks are included because the feature does not require server changes.

## Phase 1: Setup

**Purpose**: Lock implementation to the approved narrow increment and identify
reuse points before editing code.

- [X] T001 Review `specs/004-answer-topology-sources/spec.md`, `plan.md`, `research.md`, `data-model.md`, and `contracts/*.md` to keep implementation inside the approved increment.
- [X] T002 Review and reuse the current ApeRAG answer/footer/source drawer files in `web/src/components/chat/message-parts-ai.tsx`, `web/src/components/chat/message-reference.tsx`, and `web/src/components/chat/message-reference-card.tsx`, plus the Mermaid renderer in `web/src/components/chart-mermaid.tsx`.

---

## Phase 2: Foundational

**Purpose**: Restore the approved answer structure and clean up the shared
reference-row shaping used by the drawer.

- [X] T003 Rewrite source-row preparation in `web/src/components/chat/message-answer-support.types.ts` so it produces one clean row per source with trustworthy locator hints and no answer-graph-only coupling.
- [X] T004 [P] Clean preview-title formatting in `aperag/agent/tool_reference_extractor.py` and update `tests/unit_test/agent/test_tool_reference_extractor.py` to cover the source-row metadata contract used by the drawer.

**Checkpoint**: Source rows are clean enough to drive the drawer UI and the extractor contract is verified.

---

## Phase 3: User Story 1 - Keep ApeRAG Answer Structure (Priority: P1) MVP

**Goal**: Restore the answer footer/source workflow to the ApeRAG structure and remove the extra inline support block.

**Independent Test**: Open a chat answer and verify there is no extra inline `Knowledge Graph` support block; sources are accessed through the ApeRAG-style source entry again.

### Implementation for User Story 1

- [X] T005 [US1] Update `web/src/components/chat/message-parts-ai.tsx` to remove the inline `MessageAnswerSupport` render path and reconnect `MessageReference` in the answer footer.
- [X] T006 [US1] Update `web/src/components/chat/message-reference.tsx` so the source drawer entry stays visually close to ApeRAG while showing the upgraded drawer content.

**Checkpoint**: The answer page is back to the approved ApeRAG interaction shape.

---

## Phase 4: User Story 2 - View a Better-Looking Existing Topology (Priority: P1)

**Goal**: Keep the existing Mermaid topology content but render it with a more refined MiroFish-like visual shell.

**Independent Test**: Open an answer containing `流程拓扑` and verify the graph content is unchanged while the render looks upgraded and still supports raw Mermaid data fallback.

### Implementation for User Story 2

- [X] T007 [US2] Refine `web/src/components/chart-mermaid.tsx` to keep the existing Mermaid graph/data flow while upgrading only the visual shell, controls, and fallback presentation.
- [X] T008 [P] [US2] Refine `web/src/components/chart-mermaid.css` so the topology block gets the approved MiroFish-like rendering treatment without changing graph generation.

**Checkpoint**: Existing answer topology renders through the same Mermaid path with improved visual quality.

---

## Phase 5: User Story 3 - Inspect Sources Row by Row (Priority: P2)

**Goal**: Show one collapsible row per source inside the ApeRAG drawer and identify the best available supporting location.

**Independent Test**: Open the source drawer for an answer and verify each source appears as its own expandable row with document identity and an exact-or-approximate locator.

### Implementation for User Story 3

- [X] T009 [US3] Update `web/src/components/chat/message-reference-card.tsx` to render one-row-per-source collapsible cards with ApeRAG-like styling and explicit approximate-location fallback.
- [X] T010 [US3] Keep the source drawer copy aligned in `web/src/i18n/en-US.json` and `web/src/i18n/zh-CN.json` only if changed behavior requires wording updates.

**Checkpoint**: The drawer body supports row-by-row source inspection without leaving the current answer context.

---

## Phase 6: Verification & Polish

**Purpose**: Prove the narrowed increment works and record completion.

- [X] T011 Run `uv run --extra test python -m pytest tests/unit_test/agent/test_tool_reference_extractor.py -q`.
- [X] T012 Run `corepack yarn lint` in `web/`.
- [X] T013 Run `corepack yarn build` in `web/`.
- [X] T014 Perform a local smoke validation for restored answer footer, source drawer, row expansion, and topology rendering; then update this file to mark completed work.

---

## Dependencies & Execution Order

- Phase 1 must complete before implementation edits.
- Phase 2 must complete before the source drawer UI changes.
- US1 can start after Phase 2 and restores the approved answer structure.
- US2 can proceed once the answer structure is restored because it only changes the Mermaid renderer.
- US3 depends on Phase 2 and the restored drawer flow from US1.
- Verification runs after all implementation tasks are complete.

## Parallel Opportunities

- T004 can run in parallel with T003 after the implementation approach is fixed.
- T008 can run in parallel with T007 once the topology renderer structure is settled.
- T012 and T013 can run in parallel after code changes settle.

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational tasks.
2. Restore the ApeRAG answer/source structure (US1).
3. Validate that the extra inline support block is gone.

### Incremental Delivery

1. Restore answer structure.
2. Upgrade topology rendering without changing generation.
3. Upgrade source drawer rows.
4. Run verification and smoke checks.

## Notes

- Keep code changes narrow and avoid deleting unrelated `003` artifacts unless they directly block the approved `004` behavior.
- The best available locator may be exact or approximate; never imply more precision than the current metadata supports.
- Verification completed on 2026-03-22 with `pytest`, `corepack yarn lint`, `corepack yarn build`, `docker compose up -d --build frontend api`, and a Playwright smoke check against `http://127.0.0.1:36130/workspace/bots/botf2fb2e1b48bdf5c8/chats/chat06640ca51d913d4d`.
