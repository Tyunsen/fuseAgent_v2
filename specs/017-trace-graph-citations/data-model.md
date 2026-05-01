# Data Model: Trace Graph Citations

## Time Trace Event Item

- **Purpose**: Represents one gantt task rendered in time mode.
- **Fields**:
  - `title`
  - `statement`
  - `time_label`
  - `time_precision`
  - `source_row_ids`
- **Rules**:
  - `title` must be a user-readable event phrase, not an internal label like `时间结论1`.
  - `time_precision` must preserve the best evidence-backed granularity: day, month, year, or interval-derived fallback.
  - Different evidence-backed dates must not collapse into the same rendered day unless the underlying evidence is actually the same day.

## Inline Citation Anchor

- **Purpose**: A clickable `[n]` marker embedded in answer prose.
- **Fields**:
  - `index`
  - `row_ids`
  - `display_token`
  - `interaction_target`
- **Rules**:
  - `display_token` must use the format `[n]`.
  - Clicking the anchor must open the right-side `参考文档来源` drawer and focus the matching evidence row.
  - No anchor may be rendered when there is no actual mapped source row.

## Source Drawer Focus State

- **Purpose**: Tracks source drawer open/focus behavior across action-row clicks, graph clicks, and inline citation clicks.
- **Fields**:
  - `sources_open`
  - `requested_row_id`
  - `request_version`
  - `active_row_ids`
  - `expanded_row_ids`
- **Rules**:
  - Any citation or graph click must be able to request a focus change even if the drawer is already open.
  - Focusing one row must not destroy the full ordered evidence list.

## Answer-Scoped Entity Subgraph

- **Purpose**: The entity-mode knowledge-graph subset for the current answer.
- **Fields**:
  - `nodes`
  - `edges`
  - `linked_row_ids`
  - `focus_label`
  - `groups`
- **Rules**:
  - Nodes and edges must be drawn from graph elements linked to the current answer, not from the whole collection indiscriminately.
  - When direct mapping fails, fallback matching may widen selection, but the output must remain scoped to answer-relevant entities.
  - Empty output is only valid after all configured fallback matching paths fail.

## Prepared Reference Row

- **Purpose**: Canonical answer-local evidence row derived from `Reference.metadata`.
- **Fields**:
  - `id`
  - `documentName`
  - `chunkIds`
  - `sectionLabel`
  - `previewTitle`
  - `snippet`
  - `text`
  - `sourceHref`
- **Rules**:
  - Row order must remain stable within one rendered answer because citation numbering depends on it.
  - `chunkIds`, document identity, and visible text are all valid matching signals for graph linking and citation binding.
