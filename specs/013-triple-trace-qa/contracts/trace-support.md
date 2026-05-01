# Contract: Trace Support Response

## Scope

This contract defines the post-answer backend response that powers
conclusion-level citations and the mode-specific trace graph.

## Contract

1. The backend MUST expose a collection-scoped trace-support endpoint separate from the main streaming answer path.
2. The request MUST include:
   - the selected `trace_mode`
   - the user question
   - the final answer text or answer markdown
   - the current answer's reference rows or equivalent source-row inputs
3. The response MUST include:
   - `trace_mode`
   - `conclusions`: discrete answer findings with `id`, `statement`, and `source_row_ids`
   - `graph`: a mode-specific graph payload
   - `fallback_used`: whether weaker organization was required because structured evidence was incomplete
4. Each returned conclusion MUST bind to one or more existing source rows.
5. The `graph` payload MUST be meaningfully different across `time`, `space`, and `entity` modes:
   - `time`: temporal order or grouping
   - `space`: location-centered grouping
   - `entity`: focal-entity-centered organization
6. When structured evidence is insufficient, the response MUST still return usable conclusions and clearly indicate fallback behavior rather than failing silently.
7. The trace-support response MUST stay consistent with the answer text and with the visible citation drawer entries derived from the same references.
