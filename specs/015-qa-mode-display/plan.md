# Implementation Plan: QA Mode Display

**Branch**: `015-qa-mode-display` | **Date**: 2026-04-04 | **Spec**: [spec.md](E:/codes/fuseAgent_v2/fuseAgent/specs/015-qa-mode-display/spec.md)  
**Input**: Feature specification from [spec.md](E:/codes/fuseAgent_v2/fuseAgent/specs/015-qa-mode-display/spec.md)

## Summary

Refine the current knowledge-base QA presentation without replacing the existing backend retrieval stack. The implementation will keep answer text streamed, unify visible citations across all modes, collapse the source list into one default-closed “本次回答文档来源” panel, remove duplicate summary/conclusion/source cards from the answer shell, keep time mode on gantt, keep space mode shell-compatible with default `graph TD`, render entity mode with the existing knowledge-graph component instead of Mermaid, and restore visible per-document MiroFish graph status with 15-second auto-refresh only while the collection graph is building.

## Technical Context

**Language/Version**: Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend  
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy-backed services, existing WebSocket chat flow, existing trace-support service, existing answer graph service, Next.js 15, next-intl, Tailwind CSS 4, `react-force-graph-2d`, Mermaid  
**Storage**: PostgreSQL metadata, existing vector store, Elasticsearch fulltext index, Neo4j-backed MiroFish graph data, existing `Reference.metadata` for answer source binding  
**Testing**: Targeted `pytest`, `python -m compileall`, `corepack yarn lint`, `corepack yarn build`, remote browser/runtime smoke checks, recurring full acceptance via `scripts/run_triple_trace_acceptance.py`  
**Target Platform**: Linux-hosted full-stack web app with Windows development workspace and remote deployment through Docker Compose  
**Project Type**: Full-stack web application  
**Performance Goals**: Preserve current answer streaming feel, keep post-answer support rendering responsive, keep document-list polling bounded to 15-second intervals only during graph build, and preserve the recurring `iw_docs` acceptance build budget of 4 minutes or less  
**Constraints**: No new top-level subsystem, no regression to default QA quality, no Mermaid fallback for entity mode, no removal of visible document-level graph status, reuse current answer/reference/graph flows, preserve Chinese-first copy, and keep the approved graph workbench UI baseline intact  
**Scale/Scope**: Chat answer presentation, inline citation affordances, trace-support UI composition, mode-specific graph rendering, and collection document status visibility/refresh behavior

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Acceptance plan identifies that this feature changes QA behavior and UI surfaces, so it MUST re-import all documents from `E:\codes\fuseAgent_v2\iw_docs` and verify the full-index completion budget stays within 4 minutes.
- [x] Validation plan states the collection graph thresholds that remain mandatory for sign-off: rendered graph page, node count > 80, edge count > 100.
- [x] QA mode validation is explicit for default, time, space, and entity modes, including the current constitution rule that space mode stays shell-compatible with default mode and uses `graph TD`.
- [x] UI work names the approved baseline branch/reference `ui-satisfied-graph-workbench` and keeps new work isolated from that branch.
- [x] Post-implement validation names the service startup/restart path, local port-forward URLs, and runtime verification path for the changed frontend/backend surfaces.
- [x] Remote verification will use the real deployment stack under `/home/common/jyzhu/ucml/fuseAgent-current` and the forwarded local URLs `http://127.0.0.1:46130/` and `http://127.0.0.1:46180/docs`.

## Phase 0 Research

See [research.md](E:/codes/fuseAgent_v2/fuseAgent/specs/015-qa-mode-display/research.md). Key decisions:

1. Keep the current WebSocket/stream formatter path as the streaming foundation; avoid introducing a second answer transport.
2. Reuse the existing trace-support request and evidence row model for all modes, but simplify the frontend shell so answer support stops duplicating summary, conclusion, and source surfaces.
3. Keep time mode on Mermaid gantt, keep default and space mode on Mermaid `graph TD`, and move entity mode to the existing force-graph-style renderer already used for answer-linked graph payloads.
4. Treat inline citations and the source list as one unified evidence surface; remove standalone answer-support “来源” duplication.
5. Restore document-level graph status visibility in the document table while keeping collection-level graph state as the backend source of truth.
6. Implement document-page polling in the client only while the collection graph status is building/updating and stop once the graph reaches a terminal non-building state.

## Phase 1 Design

### Data Model

See [data-model.md](E:/codes/fuseAgent_v2/fuseAgent/specs/015-qa-mode-display/data-model.md).

### Interface Contracts

See [chat-answer-display.md](E:/codes/fuseAgent_v2/fuseAgent/specs/015-qa-mode-display/contracts/chat-answer-display.md) and [document-graph-status-refresh.md](E:/codes/fuseAgent_v2/fuseAgent/specs/015-qa-mode-display/contracts/document-graph-status-refresh.md).

### Quickstart

See [quickstart.md](E:/codes/fuseAgent_v2/fuseAgent/specs/015-qa-mode-display/quickstart.md).

## Project Structure

### Documentation (this feature)

```text
specs/015-qa-mode-display/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- chat-answer-display.md
|   `-- document-graph-status-refresh.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
aperag/
|-- agent/
|   `-- stream_formatters.py
|-- service/
|   |-- agent_chat_service.py
|   `-- trace_answer_service.py
`-- chat/
    `-- history/
        `-- message.py

web/
|-- src/
|   |-- components/
|   |   `-- chat/
|   |       |-- message-part-ai.tsx
|   |       |-- message-parts-ai.tsx
|   |       |-- message-answer-support.tsx
|   |       |-- message-answer-graph.tsx
|   |       |-- message-reference.tsx
|   |       `-- message-reference-card.tsx
|   |-- app/
|   |   `-- workspace/
|   |       `-- collections/
|   |           |-- tools.ts
|   |           `-- [collectionId]/
|   |               `-- documents/
|   |                   |-- page.tsx
|   |                   |-- collection-index-overview.tsx
|   |                   |-- document-index-status.tsx
|   |                   `-- documents-table.tsx
|   `-- i18n/
|       |-- en-US.json
|       `-- zh-CN/page_chat.json
`-- build/
```

**Structure Decision**: Extend the existing chat rendering components and document page in place. No new top-level module is needed; the feature is presentation and status-refresh refinement on top of the already-added trace stack.

## Implementation Strategy

### Phase 1: Answer Shell Simplification And Unified Evidence Surface

- Update backend answer guidance in `aperag/service/trace_answer_service.py` and any answer post-processing rules so default/time/space/entity modes no longer instruct the model to emit duplicate summary/conclusion/source sections.
- Keep streaming behavior on the current WebSocket path in `aperag/service/agent_chat_service.py` and related message formatting utilities.
- Update `web/src/components/chat/message-parts-ai.tsx`, `message-part-ai.tsx`, `message-reference.tsx`, and `message-reference-card.tsx` so inline references remain visible while the single source list becomes the only expandable source surface and is collapsed by default.
- Remove duplicate answer-support summary/conclusion/source card rendering from `web/src/components/chat/message-answer-support.tsx`.

### Phase 2: Mode-Specific Graph Rendering Cleanup

- Keep default mode on the current Mermaid topology/process graph path.
- Keep time mode on Mermaid gantt.
- Keep space mode shell-compatible with default mode and render the same `graph TD` topology graph instead of the previous location-gantt design.
- Update entity mode so the primary graph uses the force-graph / knowledge-graph renderer in `web/src/components/chat/message-answer-graph.tsx` rather than Mermaid.
- Ensure no extra “Knowledge Graph 回答关联图谱” card remains outside the primary graph area for time/space/entity modes.

### Phase 3: Document Graph Status Visibility And Polling

- Keep document-level graph status visible in `documents-table.tsx` and `document-index-status.tsx` for MiroFish collections.
- Replace the old explanatory copy in `collection-index-overview.tsx` with copy that clarifies collection-level graph state without hiding document-level status.
- Move the document page to a client-refresh-capable shape: keep server-fetched data as initial payload, then add a 15-second refresh loop in the client while the collection graph is `building` or `updating`.
- Stop polling automatically once the graph reaches `ready`, `failed`, or another non-building state, and preserve current query params / page / filters during refresh.

### Phase 4: Verification And Deployment

- Add or update targeted tests for answer-shell simplification, trace-mode graph selection, source list behavior, and document-list polling conditions.
- Run local verification with `pytest` where applicable, `python -m compileall`, `corepack yarn lint`, and `corepack yarn build`.
- Regenerate `web/build` because remote deployment serves the built frontend artifact.
- Deploy the latest code to the remote stack under `/home/common/jyzhu/ucml/fuseAgent-current`, forward ports locally, and re-run constitution acceptance on `iw_docs`.
- Manually/automatically verify the document list shows graph status per document and only auto-refreshes during active graph build.

## Post-Design Constitution Check

- [x] The design stays inside knowledge-base QA presentation and collection/document status visibility; it does not introduce a new retrieval or graph lifecycle subsystem.
- [x] Reuse remains the default: existing WebSocket streaming, trace-support payloads, graph renderer, and document list are adapted rather than replaced.
- [x] Space mode now explicitly follows the current constitution rule instead of the older location-gantt requirement.
- [x] UI work remains constrained to approved chat and document/graph surfaces and respects the `ui-satisfied-graph-workbench` baseline rule.
- [x] Remote acceptance remains mandatory because this feature changes QA presentation and graph-related UI behavior.

## Complexity Tracking

No constitution violations require justification for this increment.
