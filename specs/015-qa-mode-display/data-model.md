# Data Model: QA Mode Display

## Answer Message Shell

- **Purpose**: Represents the visible answer container shown in chat.
- **Fields**:
  - `trace_mode`
  - `message_parts`
  - `inline_citation_markers`
  - `reference_panel_state`
  - `primary_graph_kind`
- **Rules**:
  - Must not include duplicate summary/conclusion/source cards once the simplified shell is active.

## Reference Panel State

- **Purpose**: Tracks whether the unified “本次回答文档来源” list is collapsed or expanded.
- **Fields**:
  - `default_collapsed`
  - `expanded_row_ids`
  - `active_row_ids`
- **Rules**:
  - Defaults to collapsed.
  - Expanding rows must not remove inline citation visibility.

## Trace Visualization Contract

- **Purpose**: Defines which graph renderer is used for each trace mode.
- **Fields**:
  - `trace_mode`
  - `layout`
  - `renderer_type`
- **Allowed values**:
  - `default`: `graph TD` / Mermaid topology
  - `time`: Mermaid gantt
  - `space`: `graph TD` / Mermaid topology
  - `entity`: force-graph / knowledge-graph renderer

## Document Graph Status Row

- **Purpose**: Represents the per-document graph status shown in the collection documents table.
- **Fields**:
  - `document_id`
  - `document_name`
  - `visible_graph_status`
  - `collection_graph_status`
  - `last_refreshed_at`
- **Rules**:
  - The row remains visible for every document in MiroFish collections.
  - The visible status may mirror collection graph build state when backend document-level graph status is not authoritative.

## Document Status Polling Session

- **Purpose**: Controls the document list auto-refresh lifecycle.
- **Fields**:
  - `enabled`
  - `interval_seconds`
  - `stop_when_collection_graph_status_in`
  - `preserved_query_state`
- **Rules**:
  - Poll every 15 seconds.
  - Stop once collection graph status is no longer `building` or `updating`.
  - Preserve page, filters, sorting, and search query during refresh.
