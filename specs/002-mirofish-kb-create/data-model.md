# Data Model: MiroFish-Style Knowledge Base Creation

## Knowledge Base Draft

- **Purpose**: Minimal create request entered by the user.
- **Fields**:
  - `title`: required knowledge base name
  - `description`: required knowledge base intent / business purpose
- **Validation**:
  - Both fields required
  - No advanced setup fields accepted from the create UI in this increment

## Hidden Collection Defaults

- **Purpose**: Backend-only defaults applied when creating a MiroFish-mode
  collection.
- **Fields**:
  - `type = document`
  - `source = system`
  - `language = zh-CN`
  - `embedding`: resolved default embedding model
  - `completion`: resolved default completion model
  - `enable_vector = true`
  - `enable_fulltext = true`
  - `enable_knowledge_graph = false` for the legacy ApeRAG graph-search path
  - `enable_summary = false`
  - `enable_vision = false`

## MiroFish Collection Mode

- **Purpose**: Marks a collection as using the simplified create + MiroFish
  graph workflow.
- **Fields**:
  - `creation_mode = mirofish_simple`
  - `graph_engine = mirofish`
- **Relationships**:
  - Attached to `CollectionConfig`
  - Consumed by create flow, graph service, document confirmation, and frontend
    helpers

## Graph Lifecycle State

- **Purpose**: Communicates graph readiness and current build phase to frontend
  and backend logic.
- **Fields**:
  - `graph_status`: `waiting_for_documents | building | updating | ready | failed`
  - `graph_status_message`: optional human-readable summary
  - `graph_error`: optional last failure message
  - `graph_last_synced_at`: optional timestamp
- **State transitions**:
  - On collection create: `waiting_for_documents`
  - On first confirmed docs: `building`
  - On later confirmed docs: `updating`
  - On successful run: `ready`
  - On failure: `failed`

## Graph Revision

- **Purpose**: Prevent stale graph jobs from replacing newer results.
- **Fields**:
  - `graph_revision`: integer monotonically increasing per build/update request
  - `active_graph_revision`: integer of the currently active graph
  - `active_graph_id`: revision-specific graph identifier used for reads
- **Rules**:
  - Each build/update increments `graph_revision`
  - Only the latest successful revision may update `active_graph_*`

## Collection Document Build Context

- **Purpose**: Input assembled from current collection documents for ontology
  generation and graph rebuild.
- **Fields**:
  - `collection_id`
  - `document_ids`
  - `document_name`
  - `parsed_content`
  - `combined_text`
  - `intent` sourced from collection description
- **Relationships**:
  - Derived from confirmed collection documents
  - Consumed by the MiroFish graph build service
