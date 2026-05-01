# Data Model: Gantt Source Citations

## Time Trace Event Item

- **Purpose**: Represents one gantt task shown in time mode.
- **Fields**:
  - `event_label`
  - `time_label`
  - `start_date`
  - `duration_granularity`
  - `source_row_ids`
- **Rules**:
  - `event_label` must be a human-readable event name or short event phrase.
  - `start_date` must reflect the strongest time precision supported by evidence.
  - Different evidence-backed dates must not collapse into one identical day unless the evidence itself is identical.

## Time Trace Graph Payload

- **Purpose**: Structured answer-support graph payload used by time mode.
- **Fields**:
  - `trace_mode`
  - `layout`
  - `groups`
  - `conclusions`
- **Rules**:
  - `layout` remains `timeline` for time mode.
  - Time mode consumes the main gantt visualization only; any secondary grouped-card payload must be ignored or suppressed in the view layer.

## Prepared Reference Row

- **Purpose**: Canonical answer-local source item derived from `Reference.metadata`.
- **Fields**:
  - `id`
  - `documentName`
  - `sourceHref`
  - `snippet`
  - `text`
  - `locationLabel`
- **Rules**:
  - Row order must remain stable within one answer render.
  - The same row order is reused to derive inline citation numbering.

## Inline Citation Marker

- **Purpose**: Visible `[n]` token inserted into answer prose.
- **Fields**:
  - `index`
  - `row_id`
  - `display_token`
- **Rules**:
  - `display_token` must use the format `[n]`.
  - One reference row maps to one stable `index` within a rendered answer.
  - Multiple answer statements may reuse the same `index`.

## Source Drawer State

- **Purpose**: Tracks whether the right-side source drawer is open and what evidence row is focused.
- **Fields**:
  - `open`
  - `active_row_ids`
  - `expanded_row_ids`
  - `requested_row_id`
- **Rules**:
  - The drawer can be opened from the action bar button or from graph/citation interactions.
  - Focusing one row must not lose the rest of the numbered evidence list.
