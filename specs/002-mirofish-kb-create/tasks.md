# Tasks: MiroFish-Style Knowledge Base Creation

**Input**: Design documents from `/specs/002-mirofish-kb-create/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: Verification is required for the changed create flow, document-triggered graph lifecycle, and graph/Q&A surface behavior. Targeted automated verification plus local smoke checks are included below.

## Phase 1: Setup

**Purpose**: Lock the implementation scope to the approved increment and prepare reuse-oriented artifacts.

- [X] T001 Review `specs/002-mirofish-kb-create/spec.md`, `plan.md`, `research.md`, `data-model.md`, and `contracts/*.md` to keep implementation inside the approved MiroFish-create increment.
- [X] T002 Capture concrete reuse targets from `E:\codes\fuseAgent_v2\MiroFish\backend\app\services\*.py` and `web/src/app/workspace/collections/*.tsx` before adding net-new glue code.

---

## Phase 2: Foundational

**Purpose**: Add the shared configuration and collection-mode primitives the rest of the feature depends on.

- [X] T003 Extend `aperag/schema/view_models.py`, `aperag/schema/utils.py`, and `web/src/api/models/collection-config.ts` with explicit MiroFish workflow metadata fields.
- [X] T004 Add backend helpers in `aperag/service/collection_service.py` to resolve hidden default models and build a valid MiroFish-style collection config when create requests omit advanced settings.
- [X] T005 Add frontend collection-mode helpers in `web/src/app/workspace/collections/tools.ts` so list/search/doc pages can detect MiroFish collections and compute graph readiness correctly.

**Checkpoint**: Collection-mode metadata and hidden-default plumbing are available for both backend and frontend code.

---

## Phase 3: User Story 1 - Minimal Knowledge Base Create Flow (Priority: P1)

**Goal**: Users create a knowledge base with only name and intent/description, and successful creation lands directly on the upload page.

**Independent Test**: Open `/workspace/collections/new`, confirm only the minimal fields are required, submit successfully, and verify the browser lands on `/workspace/collections/{id}/documents/upload`.

### Implementation for User Story 1

- [X] T006 [US1] Simplify `web/src/app/workspace/collections/collection-form.tsx` so the add flow submits only `title`, `description`, and `type`, while preserving the ApeRAG shell.
- [X] T007 [US1] Update `web/src/app/workspace/collections/new/page.tsx` and related messages so the create page keeps the existing ApeRAG layout but removes the old index/model setup sections.
- [X] T008 [US1] Update `aperag/service/collection_service.py` and `aperag/views/collections.py` so minimal create requests produce an initialized MiroFish-mode collection shell with hidden defaults.
- [X] T009 [US1] Redirect successful create submissions from `web/src/app/workspace/collections/collection-form.tsx` to `web/src/app/workspace/collections/[collectionId]/documents/upload`.

**Checkpoint**: Minimal create works end-to-end without exposing ApeRAG advanced setup inputs.

---

## Phase 4: User Story 2 - Document-Triggered MiroFish Graph Lifecycle (Priority: P2)

**Goal**: The first confirmed document upload starts the initial MiroFish graph build, and later uploads trigger graph updates with revision-safe status tracking.

**Independent Test**: Create a new minimal collection, confirm one staged document, verify the graph status changes from waiting to building to ready, then confirm another document and verify the status changes to updating and back to ready.

### Tests for User Story 2

- [X] T010 [P] [US2] Add targeted graph-lifecycle coverage in `tests/mirofish_graph/` for revision-safe status transitions and stale-result protection.

### Implementation for User Story 2

- [X] T011 [US2] Add the reused/adapted MiroFish graph modules under `aperag/mirofish_graph/` for ontology generation, chunk extraction, Neo4j persistence, and graph identity helpers.
- [X] T012 [US2] Implement `aperag/service/mirofish_graph_service.py` to assemble collection document text from ApeRAG parsing, build/update graphs, and map stored graph data back to the existing API shape.
- [X] T013 [US2] Register a dedicated Celery entrypoint in `config/celery_tasks.py` for MiroFish collection graph builds.
- [X] T014 [US2] Update `aperag/service/document_service.py` so document confirmation skips the old ApeRAG graph index path for MiroFish collections, advances graph lifecycle metadata, and queues the new graph task.
- [X] T015 [US2] Update `aperag/service/graph_service.py` so graph reads for MiroFish collections come from the new service instead of LightRAG.

**Checkpoint**: Confirmed uploads drive the new graph lifecycle and graph reads return the active MiroFish graph revision.

---

## Phase 5: User Story 3 - Surface the New Lifecycle Without Reintroducing Old Graph Options (Priority: P3)

**Goal**: Existing ApeRAG collection screens show the new waiting/building/updating/ready signals while hiding the old graph-search/index setup choices for MiroFish collections.

**Independent Test**: Open the collection list, documents page, upload page, search page, and graph page for a MiroFish collection and verify readiness messaging, graph entry visibility, and hidden legacy graph-search/index controls.

### Implementation for User Story 3

- [X] T016 [US3] Update `web/src/app/workspace/collections/page.tsx` and `web/src/app/workspace/collections/collection-list.tsx` to compute query access using MiroFish graph lifecycle state instead of document-only heuristics.
- [X] T017 [US3] Update `web/src/app/workspace/collections/[collectionId]/collection-header.tsx` and `web/src/app/workspace/collections/[collectionId]/graph/collection-graph.tsx` so MiroFish collections keep the graph tab but stop calling old LightRAG-only merge behavior.
- [X] T018 [US3] Update `web/src/app/workspace/collections/[collectionId]/documents/page.tsx`, `web/src/app/workspace/collections/[collectionId]/documents/upload/page.tsx`, and `web/src/app/workspace/collections/[collectionId]/documents/upload/document-upload.tsx` to surface waiting/building/updating/failed graph status copy.
- [X] T019 [US3] Update `web/src/app/workspace/collections/[collectionId]/search/page.tsx`, `web/src/app/workspace/collections/[collectionId]/search/search-table.tsx`, and `web/src/app/workspace/collections/[collectionId]/search/search-test.tsx` so Q&A gating follows the new lifecycle and the old graph-search toggle stays hidden for MiroFish collections.
- [X] T020 [US3] Update `web/src/app/workspace/collections/collection-form.tsx` edit mode so MiroFish collections keep the simplified settings surface instead of re-exposing ApeRAG graph/index configuration.

**Checkpoint**: The product surfaces the MiroFish lifecycle clearly without reviving the old ApeRAG graph setup UX.

---

## Phase 6: Verification & Polish

**Purpose**: Prove the increment works and record completion in the feature artifacts.

- [X] T021 Run targeted backend verification for the new graph lifecycle in `tests/mirofish_graph/`.
- [X] T022 Run `corepack yarn lint` in `web/`.
- [X] T023 Run `corepack yarn build` in `web/`.
- [X] T024 Perform a local smoke pass for create -> upload -> graph -> Q&A gating and update this file to reflect completed work.

---

## Dependencies & Execution Order

- Setup and Foundational phases must complete before the user-story work.
- US1 unlocks the user-visible create flow and should land before US2/US3 verification.
- US2 provides the backend graph lifecycle needed by US3 status surfaces.
- US3 depends on the shared collection-mode helpers from Phase 2 and the backend lifecycle from US2.
- Final verification runs after all implementation tasks are complete.

## Parallel Opportunities

- T003 and T005 can proceed in parallel after the design review.
- T010 can be written while US2 implementation is being assembled.
- T016, T017, T018, and T019 can be implemented in parallel once the backend lifecycle contract is stable.
- T022 and T023 can run in parallel after code changes settle.
