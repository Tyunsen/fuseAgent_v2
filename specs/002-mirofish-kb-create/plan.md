# Implementation Plan: MiroFish-Style Knowledge Base Creation

**Branch**: `002-mirofish-kb-create` | **Date**: 2026-03-21 | **Spec**: `E:\codes\fuseAgent_v2\fuseAgent\specs\002-mirofish-kb-create\spec.md`  
**Input**: Feature specification from `E:\codes\fuseAgent_v2\fuseAgent\specs\002-mirofish-kb-create\spec.md`

## Summary

Replace the current full ApeRAG create-knowledge-base form with a MiroFish-style
minimal flow that only collects knowledge base name and intent/description.
Keep the ApeRAG page shell and navigation style, but move hidden setup
decisions to the backend: default models are resolved automatically, the
collection is created as a shell, and the first confirmed document upload
triggers a MiroFish-derived ontology + Neo4j graph build flow. Later document
uploads trigger graph rebuild/update behavior using the same MiroFish-derived
pipeline, while vector/fulltext retrieval continues to reuse the existing
ApeRAG document and Q&A stack.

## Technical Context

**Language/Version**: Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend  
**Primary Dependencies**: FastAPI, Celery, SQLAlchemy, existing ApeRAG index pipeline, Next.js 15, next-intl, Tailwind CSS 4, Neo4j driver, OpenAI-compatible SDK, reused MiroFish graph extraction patterns  
**Storage**: PostgreSQL, Redis, Elasticsearch, Qdrant, Neo4j, object storage, collection config JSON persisted in the `collection.config` column  
**Testing**: `pytest` for targeted backend flow coverage, frontend `yarn lint`, frontend `yarn build`, and targeted local smoke verification  
**Target Platform**: Linux server deployment plus local Windows development workspace  
**Project Type**: Full-stack web application  
**Performance Goals**: Preserve the current ApeRAG collection/document/Q&A responsiveness while reusing MiroFish graph extraction concurrency defaults for document-triggered graph builds  
**Constraints**: Keep scope inside the create-flow increment; keep ApeRAG-style UI shell; do not expose old index/model toggles in the create page; reuse MiroFish graph-building behavior rather than inventing a new graph pipeline; keep Q&A stable by not forcing old graph-search behavior when the collection uses the new MiroFish graph mode  
**Scale/Scope**: Internal admin-style users, single knowledge base flows, one new create path, document-triggered graph build/update, no public or multi-tenant expansion

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Scope is limited to the approved increment and mapped to sections 1, 5.1, 6.1, 7.1, 8.1, 8.4, 10.1, and 12 of `BUSINESS-REQUIREMENTS.md`.
- [x] Out-of-scope items remain explicit: homepage redesign, document-management redesign beyond graph-state messaging, Q&A redesign, graph-UI redesign, model-admin changes, and speculative UI invention.
- [x] Reuse candidates are concrete: ApeRAG provides the page shell, collection/document/Q&A wiring, and document parsing/storage; MiroFish provides the simplified create interaction model plus ontology/Neo4j graph extraction behavior; net-new code is limited to the glue between them.
- [x] UI impact matches the spec's `UI parity-adaptation` scope.
- [x] No server-specific deployment change is required for this increment beyond existing Neo4j/model configuration already present in the stack.
- [x] Verification will prove the changed behavior for minimal create, direct post-create document upload entry, hidden ApeRAG index options, and document-triggered graph build/update status.

## Phase 0 Research

See `research.md` for the design decisions that resolve implementation unknowns.
The conclusions used by implementation are:

1. Keep ApeRAG's existing collection/document/Q&A shell and only simplify the
   create page.
2. Resolve hidden collection defaults on the backend by reusing the existing
   public default-model lookup services instead of keeping model selectors in
   the UI.
3. Store the new collection workflow state in `CollectionConfig`, because
   `collection.config` is already persisted as JSON and avoids a migration for
   this increment.
4. Trigger the graph build/update from `confirm_documents()`, because that is
   the existing point where staged uploads become real collection documents.
5. Disable the old ApeRAG graph index path for MiroFish-style collections, but
   keep vector/fulltext retrieval so Q&A remains operational.
6. Adapt MiroFish's ontology generation and Neo4j build code to run against
   parsed collection documents, rather than importing MiroFish's separate
   project/file upload workflow wholesale.

## Phase 1 Design

### Data Model

See `data-model.md`. The increment centers on:

- Minimal Knowledge Base Draft
- Hidden Collection Defaults
- MiroFish Graph State
- Active Graph Revision
- Document-triggered Graph Build Cycle

### Interface Contracts

See `contracts/create-flow.md` and `contracts/graph-lifecycle.md`.

### Quickstart

See `quickstart.md` for the local validation sequence that implementation must
pass.

## Project Structure

### Documentation (this feature)

```text
specs/002-mirofish-kb-create/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── create-flow.md
│   └── graph-lifecycle.md
└── tasks.md
```

### Source Code (repository root)

```text
aperag/
├── schema/
│   ├── utils.py
│   └── view_models.py
├── service/
│   ├── collection_service.py
│   ├── document_service.py
│   ├── graph_service.py
│   └── mirofish_graph_service.py
├── tasks/
│   ├── utils.py
│   └── mirofish_graph.py
└── views/
    └── collections.py

config/
└── celery_tasks.py

tests/
└── mirofish_graph/

web/
└── src/
    ├── app/workspace/collections/
    │   ├── collection-form.tsx
    │   ├── new/page.tsx
    │   ├── tools.ts
    │   └── [collectionId]/
    │       ├── collection-header.tsx
    │       ├── graph/collection-graph.tsx
    │       ├── documents/
    │       │   ├── page.tsx
    │       │   ├── documents-table.tsx
    │       │   └── upload/document-upload.tsx
    │       └── search/
    │           ├── search-table.tsx
    │           └── search-test.tsx
    ├── components/providers/
    │   └── collection-provider.tsx
    └── i18n/
        ├── en-US.d.json.ts
        └── zh-CN.d.json.ts
```

**Structure Decision**: Keep the existing ApeRAG repository layout. Add one
focused backend service/task pair for the MiroFish graph workflow, extend the
existing collection schema/config models, and adapt only the collection create,
document upload, graph, and Q&A-adjacent frontend files that need to understand
the new mode.

## Implementation Strategy

### Phase 1: Minimal Create Flow

- Simplify the `add` version of the collection form to title plus
  intent/description only.
- Keep the ApeRAG page shell, header, and breadcrumbs.
- Remove the old index and model configuration cards from the create path.
- Redirect successful creation directly to the collection's document upload
  page.

### Phase 2: Hidden Defaults and Collection Mode Metadata

- Extend `CollectionConfig` with explicit MiroFish-mode metadata fields.
- Resolve default embedding and completion models on the backend using the
  existing public default-model lookup services.
- Create minimal collections with vector/fulltext enabled, ApeRAG graph-search
  disabled, and MiroFish graph mode metadata initialized to
  `waiting_for_documents`.

### Phase 3: Document-triggered MiroFish Graph Lifecycle

- Hook document confirmation so the first confirmed documents trigger a graph
  build and later confirmations trigger a graph update/rebuild.
- Reuse ApeRAG's document parsing/storage path to get parsed text from all
  collection documents.
- Reuse MiroFish-style ontology generation and Neo4j graph build behavior in a
  collection-centric service.
- Track graph revision, status, and current active graph ID in collection
  config so overlapping rebuilds do not let stale runs overwrite the newest
  graph pointer.

### Phase 4: Graph/Q&A Surface Adaptation

- Show graph entry in the collection header for MiroFish-mode collections even
  though the old graph index toggle is hidden.
- Route graph data requests through a graph service branch that returns the
  MiroFish graph in the same node/edge shape the current graph UI already
  expects.
- Keep Q&A on vector/fulltext by default and suppress old graph-search options
  for MiroFish-mode collections.
- Surface waiting/building/updating/failed graph status copy in the document
  area and collection header.

## Post-Design Constitution Check

- [x] The design only changes the approved create-flow/document-triggered graph slice.
- [x] Reuse remains primary: ApeRAG for shell/data flow, MiroFish for graph-building behavior.
- [x] UI changes are limited to parity adaptation inside existing ApeRAG screens.
- [x] No speculative engine-selection or unrelated admin features were added.

## Complexity Tracking

No constitution violations require justification for this increment.
