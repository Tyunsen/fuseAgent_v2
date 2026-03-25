# Quickstart: Answer Graph And Source Cards

## Local Validation Flow

1. Start the backend, worker, and frontend for the current repo.
2. Sign in and open a knowledge-base chat that uses the existing agent bot.
3. Ask a question that returns answerable content from one collection with web
   search disabled.
4. Verify the AI answer still streams as before.
5. Verify the answer now shows an inline source card inside the answer result
   instead of only a detached reference badge/drawer.
6. Verify each cited paragraph/passage appears as its own source row.
7. Verify each source row shows document identity and passage/page context when
   available.
8. Expand or activate one source row and verify its original supporting passage
   remains inside the answer context.
9. Verify the same answer also shows a compact inline graph block when graph
   data can be resolved.
10. Click a source row and verify one or more graph elements highlight/focus.
11. Click a graph node or edge and verify the linked source rows highlight or
    are brought into view.
12. Ask a question where graph support is unavailable and verify the answer body
    and source card still render with a clear no-graph state.
13. Ask a question where only coarse source support exists and verify the source
    card explicitly says exact paragraph precision is unavailable instead of
    implying a precise citation.

## Targeted Regression Checks

- Existing chat history still loads because references remain stored in the same
  `references` message part.
- Web-search-disabled answers do not show web-only sources.
- The answer support block remains usable on 1k desktop layout.
- `corepack yarn lint`, `corepack yarn build`, and the targeted backend tests
  pass.
