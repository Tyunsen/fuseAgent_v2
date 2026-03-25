# Research: MiroFish-Style Knowledge Base Creation

## Decision 1: Keep ApeRAG document/Q&A infrastructure and only replace the create-flow contract

- **Decision**: Reuse the existing ApeRAG collection/document/Q&A pipeline and
  only simplify the collection creation input contract.
- **Rationale**: The repo already has working authentication, collection list,
  staged upload, confirmation, vector/fulltext indexing, graph page shell, and
  Q&A flows. Replacing those would exceed the approved increment.
- **Alternatives considered**:
  - Import all of MiroFish as a separate product surface. Rejected because it
    would break the constitution's unified-product constraint.
  - Keep the current full create form and hide fields visually only. Rejected
    because the backend contract would still be overexposed and harder to
    validate.

## Decision 2: Resolve default models on the backend using existing default-model services

- **Decision**: When the simplified create request omits model settings, fill
  hidden embedding and completion defaults on the backend.
- **Rationale**: Vector indexing still requires a valid embedding model, and the
  MiroFish ontology/graph build still requires a completion model. Existing
  services already discover public defaults by tag.
- **Alternatives considered**:
  - Leave models unset and rely on downstream code to infer them. Rejected
    because current vector/completion code expects explicit configuration.
  - Keep model selectors in the UI. Rejected because it violates the approved
    simplified create flow.

## Decision 3: Persist MiroFish graph workflow state in `CollectionConfig`

- **Decision**: Extend `CollectionConfig` with explicit fields for workflow
  mode, graph status, graph revision, active graph ID, and error/status copy.
- **Rationale**: `collection.config` already persists JSON, so this avoids a
  schema migration for the current increment while still making the state
  visible to frontend and backend code.
- **Alternatives considered**:
  - Add new database tables for graph projects/runs. Rejected as too heavy for
    this increment.
  - Store state only in memory or the filesystem. Rejected because the frontend
    needs stable status across requests.

## Decision 4: Trigger graph build/update from `confirm_documents()`

- **Decision**: Start the MiroFish graph job after staged documents are
  confirmed, not at raw upload time.
- **Rationale**: `confirm_documents()` is the existing moment when uploads
  become real collection documents and indexing starts, so it matches the spec's
  "first upload starts build; later uploads update graph" rule without
  reworking the staged-upload UX.
- **Alternatives considered**:
  - Trigger graph work from `upload_document()`. Rejected because uploads are
    still provisional there.
  - Require a separate "Start Graph Build" button. Rejected by the clarified
    spec.

## Decision 5: Disable the old ApeRAG graph-index workflow for MiroFish-mode collections

- **Decision**: Keep vector/fulltext indexing for retrieval, but skip the old
  LightRAG graph index path for collections created in the new mode.
- **Rationale**: The user explicitly wants MiroFish graph-building behavior. If
  both graph systems ran together, the product would waste work and produce
  ambiguous graph behavior.
- **Alternatives considered**:
  - Run both graph systems in parallel. Rejected because it duplicates cost and
    conflicts with the requirement to use MiroFish's graph path.
  - Disable vector/fulltext too. Rejected because Q&A would regress.

## Decision 6: Use revisioned graph IDs so newer rebuilds win safely

- **Decision**: Each graph build/update run writes to a revision-specific Neo4j
  graph ID, and only the latest successful revision becomes the active graph
  pointer in collection config.
- **Rationale**: This minimizes race risk when later document confirmations
  arrive while an earlier build is still running.
- **Alternatives considered**:
  - Rebuild in place using a single stable graph ID. Rejected because slower,
    stale runs could overwrite newer results.
  - Block later uploads until the current build finishes. Rejected because the
    spec explicitly allows continuing updates.
