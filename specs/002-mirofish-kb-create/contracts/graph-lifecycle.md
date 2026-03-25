# Contract: Document-triggered Graph Lifecycle

## Trigger contract

- Raw upload to `/documents/upload` only stages files.
- Confirmation through `/documents/confirm` is the trigger point for graph work.

## First confirmed documents

- If the collection is in `waiting_for_documents`, confirmation starts a graph
  build.
- Status transitions:
  - `waiting_for_documents -> building -> ready | failed`

## Later confirmed documents

- If the collection already has at least one successful graph build,
  confirmation starts a graph update/rebuild.
- Status transitions:
  - `ready -> updating -> ready | failed`
  - `failed -> updating -> ready | failed`

## Active graph read contract

- Graph reads use the `active_graph_id` stored in collection config.
- Only the newest successful revision may replace the active graph pointer.

## Q&A contract

- Vector/fulltext retrieval stays enabled.
- The old ApeRAG graph-search toggle is not exposed for MiroFish-mode
  collections.
