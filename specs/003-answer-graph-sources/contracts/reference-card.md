# Contract: Inline Reference Card

## User-facing contract

- Every answer that has references shows a visible inline source card within the
  answer result.
- Each source row represents one cited paragraph or passage.
- Clicking a row reveals or focuses the cited passage without navigating away
  from the current answer.

## Data contract

- The frontend consumes the existing `references[]` array.
- Each displayed row depends on the backend populating:
  - `metadata.source_row_id`
  - `metadata.document_name` or a fallback source label
  - `metadata.chunk_ids` when graph linking is available
  - `metadata.paragraph_precise`

## Fallback contract

- If paragraph-level precision is unavailable, the row still renders but marks
  that exact paragraph precision is unavailable.
- If no references exist, no source card is shown.

## Compatibility rule

- Old chat history entries without the new metadata must still render with a
  safe degraded source row presentation.
