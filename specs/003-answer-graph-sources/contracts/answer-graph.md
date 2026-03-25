# Contract: Answer-scoped Graph

## Endpoint contract

- Add one collection-scoped endpoint that returns a compact graph for one
  answer's cited evidence keys.
- Request carries cited chunk/source identifiers plus optional answer row IDs.
- Response returns:
  - answer-scoped nodes
  - answer-scoped edges
  - linkage metadata back to answer source rows
  - explicit empty-state information when graph support cannot be resolved

## Graph-linking contract

- Graph nodes and edges expose linkage keys so the frontend can highlight the
  related source rows.
- The backend resolves linked row IDs whenever possible, but the frontend may
  still derive matches through shared chunk IDs.

## UI contract

- The answer graph is rendered inline inside the answer support block.
- Clicking a graph node or edge highlights the linked source rows.
- Clicking a source row focuses/highlights the corresponding graph elements.

## Fallback contract

- Empty or unsupported graph results return a valid no-graph response, not a
  transport error, unless the collection itself is invalid or inaccessible.
