# Implementation Plan: Answer Graph And Source Cards

**Branch**: `003-answer-graph-sources` | **Date**: 2026-03-21 | **Spec**: `E:\codes\fuseAgent_v2\fuseAgent\specs\003-answer-graph-sources\spec.md`  
**Input**: Feature specification from `E:\codes\fuseAgent_v2\fuseAgent\specs\003-answer-graph-sources\spec.md`

## Summary

Upgrade the chat answer unit so each AI answer can show two inline support
blocks instead of the current badge-plus-drawer pattern: a visible source card
with one row per cited paragraph/passage, and a compact answer-scoped graph that
uses the approved MiroFish visual direction. Keep the existing agent chat flow,
but enrich `Reference.metadata` so the backend can return paragraph-level rows
and stable evidence-to-graph linkage keys. Add one lightweight answer-graph API
that derives a small graph from the cited chunk/source IDs, then render that
graph inline with bidirectional graph/evidence highlighting.

## Technical Context

**Language/Version**: Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend  
**Primary Dependencies**: FastAPI, Pydantic, existing agent WebSocket chat stack, existing search and graph services, Next.js 15, next-intl, Tailwind CSS 4, `react-force-graph-2d`, framer-motion, reused MiroFish graph visual patterns  
**Storage**: PostgreSQL chat/search metadata, collection config JSON, existing vector/fulltext stores, LightRAG graph storage, Neo4j-backed MiroFish graph storage  
**Testing**: Targeted `pytest`, frontend `corepack yarn lint`, frontend `corepack yarn build`, and local browser smoke validation of answer rendering  
**Target Platform**: Linux server deployment plus local Windows development workspace  
**Project Type**: Full-stack web application  
**Performance Goals**: Keep answer text streaming unchanged; render source rows from the existing references payload; fetch answer graph lazily and keep it small enough for desktop chat rendering (targeting answer-scoped graphs on the order of tens of nodes, not collection-wide graphs)  
**Constraints**: Stay inside the answer-result increment; do not redesign chat input/collection selection/retrieval flow; preserve Chinese-first UI; no web-search source leakage when web search is disabled; reuse existing ApeRAG/MiroFish graph and evidence code paths instead of inventing a separate answer engine  
**Scale/Scope**: Internal single-knowledge-base Q&A, one answer unit at a time, paragraph-level evidence rows, compact inline graph for each answer, no standalone graph page redesign

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Scope is limited to the approved increment and mapped to sections 1, 5.1, 6.2, 6.3, 6.4, 7.4, 7.5, 7.7, 7.8, 10.1, and 12 of `BUSINESS-REQUIREMENTS.md`.
- [x] Out-of-scope items remain explicit: retrieval/ranking changes, web-search policy changes, full chat page redesign, standalone graph page redesign, and speculative UI invention outside the answer result.
- [x] Reuse candidates are concrete: existing agent chat transport and answer components in this repo, current graph data/services in this repo, and MiroFish's graph visual direction plus graph-source storage patterns.
- [x] UI impact matches the spec's `UI parity-adaptation` scope.
- [x] No new server or deployment behavior is required; this is an application-layer answer rendering and data-shaping increment only.
- [x] Verification will prove inline source rows, paragraph-level preview, answer-scoped graph rendering, bidirectional graph/evidence linking, and no-graph / no-precise-passage fallbacks.

## Phase 0 Research

See `research.md` for the implementation decisions used in this plan. The key
conclusions are:

1. Keep the existing agent WebSocket message shape and enrich `Reference.metadata`
   instead of adding a brand-new answer payload format.
2. Replace the current agent tool reference extraction behavior that merges all
   search hits into one blob; emit one reference row per search result item.
3. Use chunk/source identifiers as the primary linkage contract between source
   rows and graph elements.
4. Add a focused backend answer-graph endpoint that derives a compact graph from
   cited chunk/source IDs instead of forcing the frontend to fetch or filter an
   entire collection graph.
5. Reuse the existing force-graph rendering approach from the collection graph
   page, but restyle and simplify it to match the approved MiroFish answer-card
   context.
6. Keep all unsupported cases explicit with empty-state copy instead of implying
   precise citations or graph support when the backend cannot resolve them.

## Phase 1 Design

### Data Model

See `data-model.md`. The increment centers on:

- Paragraph-level Answer Reference Row
- Answer Graph Query Contract
- Answer-scoped Graph Payload
- Evidence-to-Graph Link Map
- Inline Source Preview State

### Interface Contracts

See `contracts/reference-card.md` and `contracts/answer-graph.md`.

### Quickstart

See `quickstart.md` for the local validation sequence implementation must pass.

## Project Structure

### Documentation (this feature)

```text
specs/003-answer-graph-sources/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── answer-graph.md
│   └── reference-card.md
└── tasks.md
```

### Source Code (repository root)

```text
aperag/
├── agent/
│   └── tool_reference_extractor.py
├── schema/
│   └── view_models.py
├── service/
│   ├── answer_graph_service.py
│   ├── graph_service.py
│   └── mirofish_graph_service.py
├── mirofish_graph/
│   ├── neo4j_graph_backend.py
│   └── neo4j_queries.py
└── views/
    └── collections.py

tests/
└── unit_test/
    ├── agent/
    │   └── test_tool_reference_extractor.py
    └── answer_graph/
        └── test_answer_graph_service.py

web/
└── src/
    ├── components/chat/
    │   ├── message-answer-support.tsx
    │   ├── message-answer-graph.tsx
    │   ├── message-reference-card.tsx
    │   ├── message-parts-ai.tsx
    │   └── message-reference.tsx
    └── i18n/
        ├── en-US.d.json.ts
        └── zh-CN.d.json.ts
```

**Structure Decision**: Keep the existing repo layout. Implement one new backend
answer-graph service plus a small collection route, enrich reference extraction
and graph metadata in place, and add a compact set of chat components under the
existing answer rendering path rather than introducing a separate answer page or
new frontend module tree.

## Implementation Strategy

### Phase 1: Paragraph-Level Reference Contract

- Change agent tool reference extraction so collection/chat-file search results
  produce one `Reference` per result item, not one merged blob.
- Normalize metadata needed by the UI:
  `collection_id`, `document_id`, `document_name`, `page_idx`, `recall_type`,
  `chunk_ids`, `source_row_id`, and paragraph-precision flags.
- Keep persistence/backward compatibility by storing the richer data inside
  `Reference.metadata`.

### Phase 2: Answer-scoped Graph Data

- Add a lightweight answer-graph endpoint under the collection routes.
- Build the answer graph from the cited chunk/source IDs instead of the full
  collection graph.
- For MiroFish collections, expose chunk-backed evidence keys on nodes/edges and
  derive a compact subgraph from chunk matches.
- For LightRAG collections, reuse existing `source_id` graph metadata and
  derive a small filtered subgraph from referenced chunk IDs when available.

### Phase 3: Inline Answer Support UI

- Replace the detached reference badge/drawer with an inline answer support
  block inside the AI answer card.
- Reuse the current graph rendering stack (`react-force-graph-2d`) and existing
  collection graph styling ideas, but adapt them to a smaller MiroFish-like
  answer card with Chinese-first copy and desktop-first sizing.
- Reuse existing preview/markdown patterns for paragraph inspection, keeping the
  user inside the answer result.

### Phase 4: Bidirectional Linking and Fallbacks

- Add shared interaction state so clicking source rows focuses graph nodes/edges
  and clicking graph elements highlights or scrolls the linked evidence rows.
- Handle no-graph, no-precise-passage, and evidence-insufficient cases with
  explicit inline states.
- Keep all support blocks optional so answer text still renders when one support
  block is unavailable.

## Post-Design Constitution Check

- [x] The design only changes the approved answer-result slice.
- [x] Reuse remains primary: existing agent/chat components and graph services in this repo, with MiroFish as the visual/storage reference.
- [x] UI work is limited to parity adaptation inside the existing answer card.
- [x] No speculative collection-management, engine-switching, or deployment work was added.

## Complexity Tracking

No constitution violations require justification for this increment.
