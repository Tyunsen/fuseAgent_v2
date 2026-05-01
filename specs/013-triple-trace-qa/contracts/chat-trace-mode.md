# Contract: Chat Trace Mode

## Scope

This contract defines how chat requests select between the existing default
answer behavior and the three new trace modes.

## Contract

1. Chat requests MAY include an optional `trace_mode` field.
2. Allowed values are `default`, `time`, `space`, and `entity`.
3. When `trace_mode` is omitted, the backend MUST behave exactly like the current default mode.
4. The chat input UI MUST expose the four modes near the input action area without removing the existing submit workflow.
5. The selected `trace_mode` MUST be sent with the same chat request that already carries the user query and collection scope.
6. The backend MUST reuse the current default mixed retrieval path for all four modes.
7. Trace modes MAY add mode-specific normalization, ranking, and organization, but they MUST NOT disable existing vector, fulltext, or graph evidence channels that are already active for the collection.
