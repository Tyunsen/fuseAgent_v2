# Implementation Plan: Gantt Source Citations

**Branch**: `016-gantt-source-citations` | **Date**: 2026-04-04 | **Spec**: [spec.md](E:/codes/fuseAgent_v2/fuseAgent/specs/016-gantt-source-citations/spec.md)  
**Input**: Feature specification from [spec.md](E:/codes/fuseAgent_v2/fuseAgent/specs/016-gantt-source-citations/spec.md)

## Summary

Tighten the triple-trace QA presentation without changing the retrieval foundation. The implementation will improve time-trace conclusion binding so gantt tasks use real event labels and differentiated dates, remove the extra post-gantt group card in time mode, move the source entry into the message action bar, replace the bottom collapsed source card with a right-side drawer, and add stable inline citation markers such as `[1]` that map to the same numbered source rows shown in the drawer.

## Technical Context

**Language/Version**: Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend  
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy-backed services, existing WebSocket chat flow, existing trace-support service, existing answer graph service, Next.js 15, next-intl, Tailwind CSS 4, Mermaid, existing drawer UI primitives, `react-force-graph-2d`  
**Storage**: PostgreSQL metadata, existing vector store, Elasticsearch fulltext index, Neo4j-backed MiroFish graph data, existing `Reference.metadata`, existing stored chat message history  
**Testing**: Targeted `pytest`, `python -m py_compile`, `corepack yarn lint`, `corepack yarn build`, browser verification against forwarded remote stack, recurring `iw_docs` acceptance via `scripts/run_triple_trace_acceptance.py`  
**Target Platform**: Linux-hosted remote Docker Compose deployment with Windows development workspace and local port forwarding  
**Project Type**: Full-stack web application  
**Performance Goals**: Preserve streamed answer feel, keep time-mode graph rendering responsive after answer completion, open the source drawer within one user interaction, and preserve the recurring full-index acceptance budget of 4 minutes or less  
**Constraints**: Keep default retrieval behavior intact, do not add a new trace subsystem, reuse the current trace-support payload, preserve the approved UI baseline branch rules, keep space mode shell-compatible with default mode, and satisfy constitution graph thresholds of node count > 80 and edge count > 100 on `iw_docs`  
**Scale/Scope**: QA message rendering, trace-support conclusion derivation, time-mode graph labeling and date placement, source interaction UI, and citation formatting for answer text

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Acceptance plan identifies that this feature changes QA behavior and must re-import all documents from `E:\codes\fuseAgent_v2\iw_docs`, with a full-index completion budget of 4 minutes or less.
- [x] Validation plan keeps the required graph quality thresholds explicit for final sign-off: rendered collection graph, node count > 80, edge count > 100.
- [x] QA mode validation names the affected output contract: default mode stays intact, time mode must render a true gantt without extra secondary cards, entity and space mode keep the previously accepted shell rules.
- [x] UI work identifies the approved baseline branch/reference `ui-satisfied-graph-workbench` and keeps new work isolated in the current feature branch.
- [x] Post-implement validation names the remote restart path, local forwarded URLs, and runnable verification flow required for user-facing sign-off.
- [x] Remote verification uses the server path `/home/common/jyzhu/ucml/fuseAgent-current`, local forwarded URLs `http://127.0.0.1:46130/` and `http://127.0.0.1:46180/docs`, and recurring automated acceptance through `scripts/run_triple_trace_acceptance.py`.

## Phase 0 Research

See [research.md](E:/codes/fuseAgent_v2/fuseAgent/specs/016-gantt-source-citations/research.md). The key decisions are:

1. Keep the existing trace-support backend and answer graph pipeline; improve the conclusion/time-label derivation instead of inventing a separate gantt data service.
2. Treat the current time-mode extra button/card strip as a rendering artifact of grouped layouts and suppress it for time mode rather than introducing a second graph shell.
3. Reuse the existing right-side drawer pattern already present in the chat UI instead of keeping a bottom collapsible source panel.
4. Build inline citation markers from the already prepared reference rows so numbering remains stable across body text and source drawer.
5. Strip naked Mermaid text from the visible answer body as a defensive layer even when prompt guidance fails.

## Phase 1 Design

### Data Model

See [data-model.md](E:/codes/fuseAgent_v2/fuseAgent/specs/016-gantt-source-citations/data-model.md).

### Interface Contracts

See [time-trace-display.md](E:/codes/fuseAgent_v2/fuseAgent/specs/016-gantt-source-citations/contracts/time-trace-display.md) and [answer-source-evidence.md](E:/codes/fuseAgent_v2/fuseAgent/specs/016-gantt-source-citations/contracts/answer-source-evidence.md).

### Quickstart

See [quickstart.md](E:/codes/fuseAgent_v2/fuseAgent/specs/016-gantt-source-citations/quickstart.md).

## Project Structure

### Documentation (this feature)

```text
specs/016-gantt-source-citations/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- time-trace-display.md
|   `-- answer-source-evidence.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
aperag/
|-- service/
|   |-- trace_answer_service.py
|   |-- trace_support_service.py
|   `-- answer_graph_service.py
`-- schema/
    `-- view_models.py

tests/
`-- unit_test/
    |-- answer_graph/
    `-- service/

web/
|-- src/
|   |-- components/
|   |   `-- chat/
|   |       |-- message-part-ai.tsx
|   |       |-- message-parts-ai.tsx
|   |       |-- message-answer-support.tsx
|   |       |-- message-answer-graph.tsx
|   |       |-- message-reference-card.tsx
|   |       `-- message-reference.tsx
|   `-- components/
|       `-- ui/
|           `-- drawer.tsx
`-- build/
```

**Structure Decision**: Extend the current backend/frontend chat rendering stack in place. The feature is a presentation and evidence-binding refinement on top of the existing triple-trace implementation, so no new top-level module is needed.

## Implementation Strategy

### Phase 1: Time-Trace Conclusion And Gantt Quality

- Refine `aperag/service/trace_support_service.py` so time conclusions prefer event names and event-specific dates over generic normalized focus labels.
- Improve `aperag/service/trace_answer_service.py` prompt guidance so time mode does not emit `graph TD` or generic numbered time-conclusion labels.
- Update `web/src/components/chat/message-answer-graph.tsx` so time-mode gantt rendering does not append the extra grouped card strip below the main graph.
- Keep space and entity grouped behaviors unchanged unless a shared helper requires a safe refactor.

### Phase 2: Inline Citation Numbering

- Add a stable answer-level citation numbering pass in the chat UI using the prepared reference row order.
- Ensure inline citation markers are appended to visible answer sentences without corrupting markdown rendering.
- Reuse the same numbering in the source drawer rows so body and drawer remain aligned.
- Keep the no-reference case clean: no fake markers and no empty evidence entry.

### Phase 3: Source Entry And Right Drawer

- Move the evidence entry into the message action row beside timestamp / feedback / copy in `message-parts-ai.tsx`.
- Replace the bottom collapsed source card in `message-answer-support.tsx` with a controlled right-side drawer.
- Ensure graph clicks, citation-chip clicks, and the action-bar button can all open the same drawer and focus the relevant row.
- Reuse the existing drawer component rather than creating a new surface.

### Phase 4: Verification, Build Artifacts, And Remote Acceptance

- Add or update targeted tests for time-trace prompt guidance and trace-support conclusion/time-label selection.
- Run local verification with targeted `pytest`, `corepack yarn lint`, and `corepack yarn build`.
- Regenerate `web/build` because the remote frontend image is built from `web/build` inside the `web` context.
- Deploy to `/home/common/jyzhu/ucml/fuseAgent-current`, restore local forwarding, and verify:
  - time mode renders a gantt with real event labels
  - time mode no longer shows extra secondary cards
  - the action bar contains a source entry beside feedback/copy
  - clicking the source entry opens a right-side drawer
  - inline citation markers and drawer numbering match
- Re-run `python scripts/run_triple_trace_acceptance.py --skip-remote-deploy` after deployment to preserve constitution sign-off.

## Post-Design Constitution Check

- [x] The design stays inside the existing QA and trace-support stack; it does not add a new event service, retrieval path, or storage layer.
- [x] Reuse remains the default: existing trace-support, answer graph rendering, reference-row preparation, and drawer UI are adapted rather than replaced.
- [x] The affected QA-mode contract is explicit: time-mode main graph quality is corrected while default/space/entity behavior remains bounded by the current constitution.
- [x] UI work remains isolated to the current feature branch and respects the `ui-satisfied-graph-workbench` baseline rule.
- [x] Remote verification and automated acceptance remain first-class requirements for sign-off.

## Complexity Tracking

No constitution violations require justification for this increment.
