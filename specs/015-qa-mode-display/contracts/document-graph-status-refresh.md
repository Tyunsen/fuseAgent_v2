# Contract: Document Graph Status Refresh

## Scope

Defines the document-list status visibility and refresh behavior for MiroFish collection builds.

## Contract

1. The collection documents table MUST show a graph status cell for every document in a MiroFish collection.
2. The UI MUST NOT replace the document-level graph status column with explanatory copy about collection-only ownership.
3. While the collection graph status is `building` or `updating`, the document page MUST refresh status data every 15 seconds.
4. Once the collection graph status becomes `ready`, `failed`, or another non-building state, auto-refresh MUST stop automatically.
5. Auto-refresh MUST preserve the current search params, pagination, sorting, and row expansion state.
6. Collection-level graph state remains the acceptance source of truth; visible per-document status is a UX requirement, not a change to backend graph lifecycle ownership.
