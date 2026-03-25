# Contract: Navigation and UI Entry Points

## Route Contract

### `GET /`

- Authentication: Unauthenticated users may be redirected downstream by the workspace auth gate.
- Behavior:
  - MUST NOT render the ApeRAG marketing/intro page.
  - MUST redirect into `/workspace/collections`.

### `GET /workspace`

- Authentication: Required
- Behavior:
  - Redirects to `/workspace/collections`.

### `GET /workspace/collections`

- Authentication: Required
- Behavior:
  - Render the Chinese-first knowledge base homepage.
  - Show list/search/create entry.
  - Show empty states when there are no knowledge bases or search matches.
  - Each knowledge base entry exposes:
    - document management action -> `/workspace/collections/{collectionId}/documents`
    - Q&A action -> `/workspace/collections/{collectionId}/search`

### `GET /workspace/collections/new`

- Authentication: Required
- Behavior:
  - Render the reused full ApeRAG collection creation form.

### `GET /workspace/collections/{collectionId}/documents`

- Authentication: Required
- Behavior:
  - Render the reused document management workspace for the selected collection.

### `GET /workspace/collections/{collectionId}/search`

- Authentication: Required
- Behavior:
  - Render the reused per-collection query/Q&A workspace.
  - If the collection has not completed its first build, block query execution and explain why.
  - If the collection is processing incremental updates, allow query execution and show a stale-results warning.

## Header Contract

- Shared top-right controls in the adapted shell MUST contain only the authenticated user menu.
- The following controls MUST NOT be visible:
  - GitHub link
  - Docs/help link
  - Locale switcher
  - Theme switcher

## Locale Contract

- First-visit default locale MUST be `zh-CN`.
- No visible header locale switcher is required in this increment.
