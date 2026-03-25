# Quickstart: MiroFish-Style Knowledge Base Creation

## Local Validation Flow

1. Start the backend, worker, and frontend as usual for the current repo.
2. Sign in and open `/workspace/collections`.
3. Click the knowledge-base create button.
4. Verify the create page only asks for knowledge base name and intent/description.
5. Verify the old ApeRAG index/model setting sections do not appear.
6. Submit the form.
7. Verify the browser lands directly on `/workspace/collections/{collectionId}/documents/upload`.
8. Verify the collection shows a waiting-for-documents / next-step message before any document is confirmed.
9. Upload and confirm one document.
10. Verify the collection graph status changes to building, then to ready when the background task completes.
11. Verify Q&A remains available through vector/fulltext retrieval and does not expose the old graph-search toggle for this collection mode.
12. Upload and confirm another document.
13. Verify the graph status changes to updating, then back to ready.
14. Open the graph page and verify nodes/edges load from the new MiroFish graph path.

## Targeted Regression Checks

- Existing non-MiroFish collections still keep their current create/config behavior.
- Existing document list and staged upload flows still work.
- The create page remains usable on 1k desktop layout.
- `yarn lint`, `yarn build`, and the targeted backend test suite pass.
