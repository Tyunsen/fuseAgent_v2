# Tasks: Knowledge Base Triple Trace QA

**Input**: Design documents from `/specs/013-triple-trace-qa/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Verification is required because this increment changes extraction, chat request transport, answer organization, visible citations, and graph presentation. Targeted backend tests plus frontend lint/build and runtime smoke checks are included below.

## Constitution Requirements

- Tasks stay inside knowledge-base QA and must not introduce a global system intent layer.
- Reuse/adaptation tasks come before net-new subsystems.
- UI work is limited to the approved mode selector, answer support, citations, and mode-specific graph presentation.
- If UI work continues, it must use `ui-satisfied-graph-workbench` as the approved baseline and must not directly modify that correct branch.
- Remote verification must account for the actual deployment stack in `docker-compose.deploy.remote.yml` and the built frontend artifact in `web/build/`.

## Phase 1: Setup

**Purpose**: Lock implementation to the approved increment and identify concrete reuse targets before editing code.

- [X] T001 Review `specs/013-triple-trace-qa/spec.md`, `specs/013-triple-trace-qa/plan.md`, `specs/013-triple-trace-qa/research.md`, `specs/013-triple-trace-qa/data-model.md`, `specs/013-triple-trace-qa/contracts/chat-trace-mode.md`, `specs/013-triple-trace-qa/contracts/reference-metadata.md`, `specs/013-triple-trace-qa/contracts/trace-support.md`, and `specs/013-triple-trace-qa/quickstart.md` to keep implementation inside the approved increment.
- [X] T002 Capture concrete reuse targets from `aperag/mirofish_graph/ontology_generator.py`, `aperag/mirofish_graph/graph_extractor.py`, `aperag/service/prompt_template_service.py`, `aperag/service/answer_graph_service.py`, `web/src/components/chat/chat-input.tsx`, and `web/src/components/chat/message-answer-support.tsx` before editing code.
- [ ] T002A If UI work continues, create a new isolated working branch or equivalent isolated workspace from `ui-satisfied-graph-workbench` instead of modifying the approved baseline branch directly.

---

## Phase 2: Foundational

**Purpose**: Add the shared transport, fixtures, and trace-support contracts that block all user stories.

**⚠️ CRITICAL**: No user story work should start until this phase is complete.

- [X] T003 Add shared trace-mode and trace-support Pydantic models in `aperag/schema/view_models.py`.
- [X] T004 [P] Prepare reusable trace QA fixtures for questions, reference rows, and graph evidence in `tests/unit_test/conftest.py`.
- [X] T005 [P] Add shared frontend trace support state and helper types in `web/src/components/chat/message-answer-support.types.ts`.
- [X] T006 Create shared backend orchestration scaffolding in `aperag/service/trace_answer_service.py` and `aperag/service/trace_support_service.py`.
- [X] T007 Regenerate or align frontend API bindings for trace-mode chat payloads in `web/src/api/models/agent-message.ts`, `web/src/api/models/index.ts`, and `web/src/api/apis/default-api.ts`.

**Checkpoint**: Shared request/response contracts, fixtures, and trace-support scaffolding are ready for story work.

---

## Phase 3: User Story 1 - Ask in Default or Trace Mode (Priority: P1) MVP

**Goal**: Preserve the current default answer mode while adding selectable time, space, and entity modes that still reuse mixed retrieval.

**Independent Test**: Open a knowledge-base chat, ask the same question with no mode selected and with `time`, `space`, and `entity` selected, and verify default behavior remains intact while each trace mode reorganizes the answer around its own dimension.

### Tests for User Story 1

- [X] T008 [P] [US1] Add trace-mode transport and prompt regression coverage in `tests/unit_test/service/test_agent_chat_trace_mode.py`.

### Implementation for User Story 1

- [X] T009 [US1] Extend `aperag/service/agent_chat_service.py` and `aperag/service/prompt_template_service.py` so omitted `trace_mode` preserves current default behavior and selected modes inject time/space/entity answer guidance.
- [X] T010 [US1] Implement mode-aware normalization and mixed-retrieval reuse in `aperag/service/trace_answer_service.py` and `aperag/service/collection_service.py`.
- [X] T011 [US1] Wire the chat request payload for `trace_mode` in `web/src/components/chat/chat-input.tsx`, `web/src/components/chat/chat-messages.tsx`, and `web/src/app/workspace/bots/[botId]/chats/[chatId]/page.tsx`.
- [X] T012 [P] [US1] Add visible mode labels and selector copy in `web/src/components/chat/message-parts-ai.tsx`, `web/src/i18n/zh-CN.json`, and `web/src/i18n/en-US.json`.

**Checkpoint**: Users can intentionally switch between default mode and the three trace modes without breaking the current QA entry flow.

---

## Phase 4: User Story 2 - Preserve Time and Place in Extraction (Priority: P1)

**Goal**: Keep broader ontology coverage and preserve evidence-backed time/place attributes on extracted entities and relationships.

**Independent Test**: Rebuild extraction for documents that contain explicit dates, periods, locations, and aliases, then verify extracted entities/relationships retain supported time/place attributes and do not fabricate missing ones.

### Tests for User Story 2

- [X] T013 [P] [US2] Add ontology coverage for base-plus-supplemental type generation in `tests/unit_test/mirofish_graph/test_ontology_generator.py`.
- [ ] T014 [P] [US2] Add extraction coverage for evidence-backed time/place attributes in `tests/unit_test/mirofish_graph/test_graph_extractor.py` and `tests/unit_test/mirofish_graph/test_mirofish_graph_service.py`.

### Implementation for User Story 2

- [X] T015 [US2] Define fixed broad base type catalogs and higher accepted type caps in `aperag/mirofish_graph/constants.py` and `aperag/mirofish_graph/ontology_generator.py`.
- [X] T016 [US2] Implement lightweight supplemental type generation, deduplication, and canonical relation naming in `aperag/mirofish_graph/ontology_generator.py` and `aperag/service/mirofish_graph_service.py`.
- [X] T017 [US2] Preserve evidence-backed time/place attributes on entities and relationships in `aperag/mirofish_graph/graph_extractor.py` and `aperag/mirofish_graph/helpers.py`.
- [X] T018 [US2] Keep extracted source-traceability aligned with the stronger attribute flow in `aperag/service/mirofish_graph_service.py` and `aperag/agent/tool_reference_extractor.py`.

**Checkpoint**: Graph extraction keeps broader ontology coverage and retains explicit time/place evidence without inventing unsupported attributes.

---

## Phase 5: User Story 3 - Verify Conclusions with Trace Graphs and Citations (Priority: P2)

**Goal**: Bind major conclusions to concrete source rows and render clearly different time, space, and entity trace graphs in the answer flow.

**Independent Test**: Ask a question in each trace mode, then verify each major conclusion exposes at least one supporting citation and the graph changes organization by time, space, or focal entity rather than only highlighting the same topology.

### Tests for User Story 3

- [X] T019 [P] [US3] Add trace-support backend coverage in `tests/unit_test/answer_graph/test_trace_support_service.py`.
- [X] T020 [P] [US3] Add locator-precision and conclusion-binding coverage in `tests/unit_test/agent/test_tool_reference_extractor.py` and `tests/unit_test/answer_graph/test_answer_graph_service.py`.

### Implementation for User Story 3

- [X] T021 [US3] Add the collection-scoped trace-support endpoint and request validation in `aperag/views/collections.py` and `aperag/schema/view_models.py`.
- [X] T022 [US3] Implement conclusion binding, fallback handling, and source-row linking in `aperag/service/trace_support_service.py` and `aperag/service/trace_answer_service.py`.
- [X] T023 [US3] Extend `aperag/service/answer_graph_service.py` so the shared evidence package can emit time, space, and entity graph payloads.
- [X] T024 [US3] Reuse source-row metadata for visible conclusion citations in `web/src/components/chat/message-reference.tsx` and `web/src/components/chat/message-reference-card.tsx`.
- [X] T025 [US3] Load and render post-answer trace support in `web/src/components/chat/message-answer-support.tsx` and `web/src/components/chat/message-parts-ai.tsx`.
- [X] T026 [P] [US3] Render three distinct trace graph organizations in `web/src/components/chat/message-answer-graph.tsx` and `web/src/components/chat/message-answer-support.types.ts`.

**Checkpoint**: Answers show conclusion-level citations and mode-specific graphs that stay aligned with the selected trace dimension.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Prove the increment works end-to-end, regenerate deployable artifacts, and record runtime verification.

- [ ] T026A Import the full acceptance dataset from `E:\codes\fuseAgent_v2\iw_docs` into a fresh knowledge base and verify vector/fulltext/graph indexing all finish within 4 minutes.
- [ ] T026B Verify the collection graph page for the acceptance knowledge base renders successfully and satisfies >80 nodes and >100 edges.
- [ ] T026C Verify `default` mode returns text + visible citations + topology/process graph + source list.
- [ ] T026D Verify `time` mode adds a day-level gantt view when source evidence supports it.
- [ ] T026E Verify `space` mode locks onto a single focal location and adds the location-specific time-ordered gantt chart.
- [ ] T026F Verify `entity` mode returns a subgraph containing only the entities and edges referenced by the current answer.
- [ ] T027 Run targeted backend verification for `tests/unit_test/service/test_agent_chat_trace_mode.py`, `tests/unit_test/mirofish_graph/test_ontology_generator.py`, `tests/unit_test/mirofish_graph/test_graph_extractor.py`, `tests/unit_test/mirofish_graph/test_mirofish_graph_service.py`, `tests/unit_test/answer_graph/test_trace_support_service.py`, `tests/unit_test/answer_graph/test_answer_graph_service.py`, and `tests/unit_test/agent/test_tool_reference_extractor.py`.
- [X] T028 [P] Run `corepack yarn lint` in `web/`.
- [X] T029 [P] Run `corepack yarn build` in `web/` and refresh `web/build/`.
- [X] T030 Restart and verify the latest applicable stack with `docker-compose.deploy.remote.yml`, confirm forwarded frontend/API access paths against `web/build/`, and record runtime validation notes in `specs/013-triple-trace-qa/tasks.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; start immediately.
- **Foundational (Phase 2)**: Depends on Phase 1 and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Phase 2.
- **User Story 2 (Phase 4)**: Depends on Phase 2.
- **User Story 3 (Phase 5)**: Depends on Phases 3 and 4 because it needs mode transport plus richer extraction evidence.
- **Polish (Phase 6)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1**: Can start as soon as foundational trace-mode contracts are ready.
- **US2**: Can start in parallel with US1 after Phase 2 because it works on extraction and ontology paths.
- **US3**: Should begin after US1 and US2 stabilize because it consumes both selected mode state and stronger evidence/citation data.

### Within Each User Story

- Test tasks should be written before or alongside implementation and must fail before final implementation is considered complete.
- Backend transport/contracts should settle before frontend wiring that depends on them.
- Citation and graph UI should land after the trace-support backend contract is stable.

---

## Parallel Opportunities

- T004 and T005 can run in parallel after the shared backend model shape is known from T003.
- T013 and T014 can run in parallel because ontology tests and extraction tests target different modules.
- T019 and T020 can run in parallel while the trace-support service contract is being implemented.
- T026 can run in parallel with T024 once the trace-support response shape is stable.
- T028 and T029 can run in parallel after code changes settle.

---

## Parallel Example: User Story 1

```bash
# Backend trace-mode verification and frontend mode selector work can proceed together:
Task: "Add trace-mode transport and prompt regression coverage in tests/unit_test/service/test_agent_chat_trace_mode.py"
Task: "Wire the chat request payload for trace_mode in web/src/components/chat/chat-input.tsx, web/src/components/chat/chat-messages.tsx, and web/src/app/workspace/bots/[botId]/chats/[chatId]/page.tsx"
```

## Parallel Example: User Story 2

```bash
# Ontology and extraction coverage can be developed independently:
Task: "Add ontology coverage for base-plus-supplemental type generation in tests/unit_test/mirofish_graph/test_ontology_generator.py"
Task: "Add extraction coverage for evidence-backed time/place attributes in tests/unit_test/mirofish_graph/test_graph_extractor.py and tests/unit_test/mirofish_graph/test_mirofish_graph_service.py"
```

## Parallel Example: User Story 3

```bash
# Citation and graph rendering can split once the backend response contract settles:
Task: "Reuse source-row metadata for visible conclusion citations in web/src/components/chat/message-reference.tsx and web/src/components/chat/message-reference-card.tsx"
Task: "Render three distinct trace graph organizations in web/src/components/chat/message-answer-graph.tsx and web/src/components/chat/message-answer-support.types.ts"
```

---

## Implementation Strategy

### MVP First

1. Complete Setup and Foundational tasks.
2. Complete User Story 1 to preserve default mode and expose the three trace modes.
3. Validate the chat can switch modes without regressing current default QA behavior.

### Incremental Delivery

1. Finish Setup + Foundational to stabilize contracts.
2. Deliver US1 and validate the selectable QA modes.
3. Deliver US2 and validate extraction coverage plus time/place attribute retention.
4. Deliver US3 and validate conclusion citations plus mode-specific graphs.
5. Run final verification, rebuild `web/build/`, and restart the runnable stack.

### Parallel Team Strategy

1. One lane completes Phase 1 and Phase 2.
2. After Phase 2:
   - Lane A: US1 chat transport, prompts, and selector UI
   - Lane B: US2 ontology and extraction enhancement
3. After US1 and US2 stabilize:
   - Lane C: US3 trace-support endpoint, citations, and graph rendering

---

## Notes

- Keep `default` mode behavior intact unless a requirement explicitly says otherwise.
- Do not add a global military/system intent layer anywhere in the implementation.
- Time/place attributes are optional and evidence-backed on both entities and relationships; do not infer missing values.
- Reuse current vector, fulltext, and graph evidence channels in all modes instead of creating a separate retriever.
- Before remote verification, ensure `web/build/` matches the latest frontend code because the deployment image copies built artifacts directly.

## Implementation Notes

- 2026-04-03: Completed targeted backend verification for `test_agent_chat_trace_mode.py`, `test_ontology_generator.py`, `test_graph_extractor.py`, `test_trace_support_service.py`, `test_answer_graph_service.py`, and `test_tool_reference_extractor.py` with 11 tests passing.
- 2026-04-03: `corepack yarn lint` passed in `web/`; the only remaining warning is the pre-existing `react-hooks/exhaustive-deps` warning in `src/app/workspace/providers/provider-table.tsx:223`.
- 2026-04-03: `corepack yarn build` passed in `web/` and regenerated the deployable `web/build` output.
- 2026-04-03: `tests/unit_test/mirofish_graph/test_mirofish_graph_service.py` could not be collected in the current environment because `fastapi_users` is unavailable, so T014 and T027 remain open.
- 2026-04-03: Remote stack was redeployed on `211.87.232.112` under `/home/common/jyzhu/ucml/fuseAgent-current` using `scripts/deploy-fuseagent-remote.sh`.
- 2026-04-03: Remote runtime validation passed with `docker compose -f docker-compose.deploy.remote.yml ps`, `http://127.0.0.1:36180/docs -> 200`, `http://127.0.0.1:36130/ -> 200`, and `http://127.0.0.1:36130/workspace -> 200`.
- 2026-04-03: Local SSH forwarding was started to `http://127.0.0.1:46130/` and `http://127.0.0.1:46180/docs`, and both local forwarded URLs returned `200`.
- 2026-04-03: Browser smoke verification on the forwarded frontend confirmed `/workspace/bots/bota90086b4703f07c1/chats/chat6b65c9656cb7aadc` loads and the bottom-left mode selector renders the four options `默认 / 时间脉络 / 空间脉络 / 实体脉络`; switching to `时间脉络` updates the selector state successfully.
