# Implementation Plan: Trace Graph Citations

**Branch**: `017-trace-graph-citations` | **Date**: 2026-04-05 | **Spec**: [spec.md](E:/codes/fuseAgent_v2/fuseAgent/specs/017-trace-graph-citations/spec.md)  
**Input**: Feature specification from [spec.md](E:/codes/fuseAgent_v2/fuseAgent/specs/017-trace-graph-citations/spec.md)

## Summary

Finish the unresolved triple-trace QA defects without changing the default mixed-retrieval baseline. The implementation will: remove detached citation-number buttons from the answer header, turn inline `[n]` markers into clickable evidence anchors that open and focus the right-side source drawer, improve time-mode gantt task labeling and date spread so real events land on real dates instead of collapsing into one day, and harden entity-mode graph selection so `@知识库` queries prefer a non-empty answer-scoped subgraph when the collection graph is already ready.

## Technical Context

**Language/Version**: Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend  
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy-backed services, existing WebSocket chat flow, existing trace-support service, existing answer graph service, existing chat markdown renderer, Next.js 15, next-intl, Tailwind CSS 4, Mermaid, `react-force-graph-2d`  
**Storage**: PostgreSQL metadata, existing vector store, Elasticsearch fulltext index, Neo4j-backed MiroFish graph data, existing `Reference.metadata`, existing chat history storage  
**Testing**: Targeted `pytest`, `python -m py_compile`, `corepack yarn lint`, `corepack yarn build`, browser verification against the forwarded remote stack, and full `iw_docs` acceptance via `scripts/run_triple_trace_acceptance.py`  
**Target Platform**: Linux-hosted remote Docker deployment with Windows development workspace and local port forwarding  
**Project Type**: Full-stack web application  
**Performance Goals**: Preserve streamed QA feel, keep answer-body rendering responsive after citation annotation, keep source-drawer open/focus interaction within one click, and preserve the constitution full-index budget of 4 minutes or less on `iw_docs`  
**Constraints**: Keep default mode retrieval and presentation baseline intact, keep space mode shell-compatible with default mode, only allow the three trace modes when the user explicitly `@知识库`, reuse the approved UI baseline branch rule, and satisfy constitution graph thresholds of node count > 80 and edge count > 100 on `iw_docs`  
**Scale/Scope**: Trace-support conclusion derivation, answer-graph fallback strategy, chat markdown/citation rendering, right-drawer source interaction, and remote deployment/acceptance

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Acceptance plan identifies that this feature changes QA behavior and must re-import all documents from `E:\codes\fuseAgent_v2\iw_docs`, with a full-index completion budget of 4 minutes or less.
- [x] Validation plan keeps the required graph quality thresholds explicit for final sign-off: rendered collection graph, node count > 80, edge count > 100.
- [x] QA mode validation names the output contract for default, time, space, and entity behavior, including the constitution rule that the three trace modes only apply when the user explicitly `@知识库`.
- [x] QA display validation explicitly names the strict acceptance contract for inline clickable `[n]` citations, right-side `参考文档来源` drawer behavior, time-mode single gantt readability, and entity-mode non-empty subgraph behavior for graph-ready `@知识库` queries.
- [x] UI work identifies the approved baseline branch/reference `ui-satisfied-graph-workbench` and keeps the current work isolated on `017-trace-graph-citations`.
- [x] Post-implement validation names the remote runtime authority file `E:\codes\fuseAgent_v2\服务器.txt`, the remote repo path `/home/common/jyzhu/ucml/fuseAgent-current`, the required built artifact path `/home/common/jyzhu/ucml/fuseAgent-current/web/build`, and the local forwarded URLs `http://127.0.0.1:46130/` and `http://127.0.0.1:46180/docs`.
- [x] The plan states that implementation continues in a fix/redeploy/reverify loop until all constitution-tagged strict acceptance items pass or an external blocker is proven.

## Phase 0 Research

See [research.md](E:/codes/fuseAgent_v2/fuseAgent/specs/017-trace-graph-citations/research.md). The key decisions are:

1. Keep the current `trace_support_service -> answer_graph_service -> message-answer-support` path and improve quality/fallbacks in place instead of adding a separate QA graph subsystem.
2. Treat inline citation interaction as a view-layer contract backed by existing reference-row numbering, then render those markers as clickable anchors rather than storing a new citation persistence format.
3. Generate time gantt labels from cleaned event titles and evidence-backed time normalization on the backend, with the frontend only doing safe display truncation.
4. Use progressively wider graph matching for entity mode so graph-ready collections do not prematurely fall back to empty result cards when the answer clearly references relevant entities.
5. Remote deployment must ship both source changes and regenerated `web/build`, because the remote frontend image is built from the `web` context.

## Phase 1 Design

### Data Model

See [data-model.md](E:/codes/fuseAgent_v2/fuseAgent/specs/017-trace-graph-citations/data-model.md).

### Interface Contracts

See [trace-graph-display.md](E:/codes/fuseAgent_v2/fuseAgent/specs/017-trace-graph-citations/contracts/trace-graph-display.md) and [citation-drawer-contract.md](E:/codes/fuseAgent_v2/fuseAgent/specs/017-trace-graph-citations/contracts/citation-drawer-contract.md).

### Quickstart

See [quickstart.md](E:/codes/fuseAgent_v2/fuseAgent/specs/017-trace-graph-citations/quickstart.md).

## Project Structure

### Documentation (this feature)

```text
specs/017-trace-graph-citations/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- trace-graph-display.md
|   `-- citation-drawer-contract.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
aperag/
|-- service/
|   |-- answer_graph_service.py
|   |-- trace_answer_service.py
|   `-- trace_support_service.py
`-- schema/
    `-- view_models.py

tests/
`-- unit_test/
    |-- answer_graph/
    |   |-- test_answer_graph_service.py
    |   `-- test_trace_support_service.py
    |-- mirofish_graph/
    |   `-- test_graph_extractor.py
    `-- service/
        `-- test_agent_chat_trace_mode.py

web/
|-- src/
|   |-- components/
|   |   |-- markdown.tsx
|   |   |-- knowledge-graph/
|   |   |   `-- force-graph-renderer.ts
|   |   `-- chat/
|   |       |-- message-answer-graph.tsx
|   |       |-- message-answer-support.tsx
|   |       |-- message-answer-support.types.ts
|   |       |-- message-part-ai.tsx
|   |       |-- message-parts-ai.tsx
|   |       `-- message-reference-card.tsx
|   `-- i18n/
|       |-- en-US.json
|       |-- zh-CN.json
|       |-- en-US/page_chat.json
|       `-- zh-CN/page_chat.json
`-- build/
```

**Structure Decision**: Extend the existing full-stack QA rendering and trace-support stack in place. The defect is not missing architecture; it is the quality and strict-contract completion of the current implementation.

## Implementation Strategy

### Phase 1: Citation Shell Contract

- Remove the detached top-right citation-number strip from `message-parts-ai.tsx`.
- Carry answer-level citation interaction state from the message shell into the markdown/body render path.
- Render inline `[n]` markers as clickable UI elements that open the existing right drawer and focus the matching source row.
- Keep the action-row `参考文档来源` entry as the primary drawer entry point and preserve no-reference cleanliness.

### Phase 2: Time-Mode Event Title And Timeline Quality

- Refine `trace_support_service.py` so conclusion titles and gantt task labels prefer clean event names over generic prefixes and noisy row text.
- Normalize time labels more robustly so day/month/year precision is preserved instead of collapsing to a fake single day.
- Keep the time-mode main graph as one gantt and do not reintroduce secondary grouped cards.

### Phase 3: Entity-Mode Subgraph Fallback Hardening

- Relax answer-graph matching for trace mode when row-to-graph linking is sparse but the collection graph is ready and references clearly point to the same documents/chunks/entities.
- Keep the entity-mode graph answer-scoped by deriving node/edge subsets from current-answer evidence and focus entities rather than dumping the full collection graph.
- Only return an empty entity graph when no verifiable related elements exist after fallback widening.

### Phase 4: Verification, Remote Deployment, And Constitution Sign-Off

- Add or update targeted backend tests for time-title extraction, time-label normalization, and entity-graph fallback behavior.
- Add or update frontend coverage where practical, then run `corepack yarn lint` and `corepack yarn build`.
- Sync changed source files plus regenerated `web/build` to `/home/common/jyzhu/ucml/fuseAgent-current`.
- Restart the remote stack, forward ports locally, and verify with fresh chat messages:
  - default mode remains unchanged
  - time mode shows a readable gantt with real event labels and differentiated dates
  - no detached citation strip appears in the answer header
  - inline `[n]` markers are clickable and open/focus the right-side source drawer
  - entity mode produces a non-empty answer-scoped subgraph for graph-ready `@知识库` queries
- Re-run `python scripts/run_triple_trace_acceptance.py --skip-remote-deploy` against `iw_docs` until all constitution thresholds pass.

## Post-Design Constitution Check

- [x] The design stays inside the existing QA, trace-support, answer-graph, and chat-rendering stack; no new subsystem is introduced.
- [x] Default mode and mixed retrieval remain the baseline; this increment only tightens trace-mode and citation contracts.
- [x] The strict acceptance loop is explicit: local tests/build, remote deployment, fresh-message browser verification, and full `iw_docs` acceptance remain mandatory.
- [x] Remote runtime authority, deployment path, and forwarded URLs are documented and treated as required sign-off context.
- [x] UI work stays isolated from the approved `ui-satisfied-graph-workbench` baseline branch.

## Complexity Tracking

No constitution violations require justification for this increment.
