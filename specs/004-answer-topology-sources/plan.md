# Implementation Plan: ApeRAG Answer Topology And Sources

**Branch**: `004-answer-topology-sources` | **Date**: 2026-03-22 | **Spec**: [spec.md](E:/codes/fuseAgent_v2/fuseAgent/specs/004-answer-topology-sources/spec.md)  
**Input**: Feature specification from [spec.md](E:/codes/fuseAgent_v2/fuseAgent/specs/004-answer-topology-sources/spec.md)

## Summary

Restore the chat answer presentation to the pre-`003-answer-graph-sources`
ApeRAG interaction shape by removing the inline answer-support block from the
AI answer card, reusing the existing ApeRAG source entry drawer, and upgrading
only two approved surfaces: the Mermaid-based `流程拓扑` renderer and the source
drawer content. Keep ApeRAG's topology generation path unchanged, adapt the
Mermaid viewer toward the approved MiroFish visual direction, and reshape the
drawer content into one-row-per-source collapsible cards with the best
available document locator.

## Technical Context

**Language/Version**: Python 3.11 backend, TypeScript 5 / React 19 / Next.js 15 frontend  
**Primary Dependencies**: FastAPI, Pydantic, existing WebSocket chat flow, Next.js 15, next-intl, Tailwind CSS 4, Mermaid, panzoom, existing ApeRAG drawer/chat components  
**Storage**: Existing chat history/reference payload storage in PostgreSQL plus current document metadata carried inside `Reference.metadata`  
**Testing**: Targeted `pytest`, `corepack yarn lint`, `corepack yarn build`, and local browser smoke validation of answer topology plus source drawer behavior  
**Target Platform**: Linux-hosted web app with local Windows development workspace  
**Project Type**: Full-stack web application  
**Performance Goals**: Preserve current answer streaming behavior, keep topology rendering client-side, and keep source drawer interactions responsive for typical answer-level reference counts  
**Constraints**: No new answer graph module, no retrieval or backend graph-generation redesign, Chinese-first behavior, preserve ApeRAG layout and entry patterns wherever possible, limit UI changes to the approved topology and source surfaces  
**Scale/Scope**: Answer-level topology viewing and answer-level source inspection for internal single-knowledge-base Q&A

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Scope is limited to the approved increment and mapped to sections 1, 3, 4.3, 6.2, 6.3, 6.4, 7.4, 7.5, 7.7, 8.1, 8.2, 10.1, and 12 of `BUSINESS-REQUIREMENTS.md`.
- [x] Out-of-scope items are explicit: no new answer graph module, no graph-generation redesign, no retrieval changes, no full chat-page redesign.
- [x] Reuse candidates are identified: existing ApeRAG answer drawer workflow, existing Mermaid topology generation/render path, existing reference metadata pipeline, and MiroFish graph styling as a rendering reference only.
- [x] UI impact matches the spec's `UI parity-adaptation` scope.
- [x] No server or deployment changes are required for this increment.
- [x] Verification will prove restored ApeRAG answer structure, upgraded topology rendering, row-by-row collapsible sources, and explicit approximate-location fallback behavior.

## Phase 0 Research

See [research.md](E:/codes/fuseAgent_v2/fuseAgent/specs/004-answer-topology-sources/research.md) for the implementation decisions used in this plan. The key conclusions are:

1. Restore the answer UI by reconnecting the existing `MessageReference` drawer and removing the inline `MessageAnswerSupport` usage from the answer card.
2. Keep Mermaid as the source of truth for `流程拓扑` and change only the viewer shell and styling in `ChartMermaid`.
3. Keep source-row shaping lightweight by reusing `Reference.metadata` and content parsing rather than inventing a new answer payload format or a new backend endpoint.
4. Use the existing ApeRAG drawer pattern as the outer interaction, but upgrade the drawer body into collapsible per-source cards with better location labels.

## Phase 1 Design

### Data Model

See [data-model.md](E:/codes/fuseAgent_v2/fuseAgent/specs/004-answer-topology-sources/data-model.md). The increment centers on:

- Existing answer topology block
- Source drawer state
- Source reference row
- Source locator

### Interface Contracts

See [topology-render.md](E:/codes/fuseAgent_v2/fuseAgent/specs/004-answer-topology-sources/contracts/topology-render.md) and [source-drawer.md](E:/codes/fuseAgent_v2/fuseAgent/specs/004-answer-topology-sources/contracts/source-drawer.md).

### Quickstart

See [quickstart.md](E:/codes/fuseAgent_v2/fuseAgent/specs/004-answer-topology-sources/quickstart.md) for the local validation sequence implementation must pass.

## Project Structure

### Documentation (this feature)

```text
specs/004-answer-topology-sources/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- topology-render.md
|   `-- source-drawer.md
`-- tasks.md
```

### Source Code (repository root)

```text
aperag/
|-- agent/
|   `-- tool_reference_extractor.py
`-- flow/
    `-- runners/
        `-- llm.py

tests/
`-- unit_test/
    `-- agent/
        `-- test_tool_reference_extractor.py

web/
`-- src/
    |-- components/
    |   |-- chart-mermaid.tsx
    |   |-- chart-mermaid.css
    |   |-- markdown.tsx
    |   `-- chat/
    |       |-- message-parts-ai.tsx
    |       |-- message-reference.tsx
    |       |-- message-reference-card.tsx
    |       `-- message-answer-support.types.ts
    `-- i18n/
        |-- en-US.json
        `-- zh-CN.json
```

**Structure Decision**: Keep the current repository layout and avoid introducing
any new feature module tree. Implement the increment by reusing the existing
chat component tree, the existing Mermaid renderer entry point, and the
existing reference metadata path.

## Implementation Strategy

### Phase 1: Restore the Approved Answer Structure

- Remove the `MessageAnswerSupport` insertion from the AI answer card.
- Reconnect the existing `MessageReference` drawer into the answer footer so the
  source entry works like ApeRAG again.
- Leave the Mermaid `流程拓扑` inside answer markdown as the existing graph entry.

### Phase 2: Upgrade the Existing Topology Renderer

- Keep Mermaid graph content generation unchanged.
- Upgrade `ChartMermaid` and its CSS shell to better match the approved
  MiroFish visual direction while preserving graph/data toggles and fallback to
  raw Mermaid data when rendering fails.
- Avoid unrelated chat layout changes outside the existing topology block.

### Phase 3: Reshape Source Drawer Content

- Rewrite source-row preparation so it produces clean per-reference rows from the
- existing `Reference.metadata` and passage text.
- Improve source location labels using the best available document metadata and
  passage-derived section hints.
- Render the drawer body as a one-row-per-source collapsible card list that
  stays visually close to ApeRAG.

### Phase 4: Verification and Cleanup

- Add or update targeted extractor tests for preview title and row metadata.
- Run frontend lint/build and validate the restored answer footer plus source
  drawer flow in the local app.
- Mark tasks complete in `tasks.md` and record any residual limitations.

## Post-Design Constitution Check

- [x] The design stays inside the approved answer topology + source presentation slice.
- [x] Reuse remains primary: existing ApeRAG chat/footer/drawer flow and existing Mermaid generation path.
- [x] UI work is limited to parity adaptation of the approved surfaces.
- [x] No speculative deployment, model, or retrieval work was added.

## Complexity Tracking

No constitution violations require justification for this increment.
