# Research: Answer Graph And Source Cards

## Decision 1: Keep the current WebSocket chat payload shape and enrich `Reference.metadata`

- **Decision**: Continue sending answer support through the existing
  `references` message part and put the new paragraph-level / graph-linking data
  in `Reference.metadata`.
- **Rationale**: The current chat pipeline, persistence model, and frontend
  history rendering already understand `references`. Expanding metadata avoids a
  larger protocol migration in this increment.
- **Alternatives considered**:
  - Add a brand-new answer support message type. Rejected because it would force
    a wider transport/history refactor.
  - Serialize graph markup directly into markdown. Rejected because it would not
    support structured graph/evidence linking.

## Decision 2: Emit one reference row per search result item

- **Decision**: Replace the current agent reference extraction behavior that
  combines all tool results into one text blob with item-level references.
- **Rationale**: The feature requires one visible source row per cited
  paragraph/passage, and that is impossible when the backend collapses several
  search hits into one combined reference.
- **Alternatives considered**:
  - Split the combined blob on the frontend. Rejected because document identity,
    chunk IDs, and precision metadata would already be lost.
  - Keep the blob and fake row boundaries heuristically. Rejected because it
    would be fragile and violate evidence traceability.

## Decision 3: Use chunk/source identifiers as the graph/evidence linking key

- **Decision**: Normalize each reference row with chunk/source identifiers, and
  expose chunk-backed evidence keys on graph nodes and edges.
- **Rationale**: The repo already stores graph provenance in chunk/source fields
  (`source_id`, `source_chunk_id`, chunk mention relationships). That is the
  most stable cross-layer contract for mapping evidence rows back to graph
  elements.
- **Alternatives considered**:
  - Link by document name only. Rejected because one document can contain many
    distinct supporting passages.
  - Link by entity label text only. Rejected because it is ambiguous and breaks
    many-to-many evidence mappings.

## Decision 4: Add a dedicated answer-graph endpoint

- **Decision**: Add a small backend endpoint that accepts answer evidence
  linkage keys and returns a compact answer-scoped graph payload.
- **Rationale**: The existing graph API is collection-centric and optimized for
  full graph or label-based exploration, not for answer-scoped evidence-driven
  slices. A dedicated endpoint avoids forcing the frontend to fetch/filter large
  graphs.
- **Alternatives considered**:
  - Reuse the full collection graph API and filter entirely on the frontend.
    Rejected because it is heavier and less reliable for answer-scoped results.
  - Precompute answer graphs during search. Rejected because it would tangle
    retrieval and presentation concerns.

## Decision 5: Reuse the existing force-graph implementation for the answer card

- **Decision**: Build the inline answer graph by adapting the current
  `react-force-graph-2d` usage from the collection graph page, while styling the
  card after the approved MiroFish visual direction.
- **Rationale**: This repo already has node coloring, sizing, focus, and hover
  behavior. Reusing that stack is faster and safer than introducing another
  graph library.
- **Alternatives considered**:
  - Import a brand-new graph visualization package. Rejected because it adds
    more surface area than needed.
  - Use static Mermaid or text-only graph output. Rejected because it would not
    meet the approved MiroFish-style graph requirement.

## Decision 6: Prefer explicit degraded states over hidden failures

- **Decision**: If graph data or paragraph precision cannot be resolved, show an
  explicit inline state instead of hiding the block or implying exact support.
- **Rationale**: The business requirement emphasizes trust, evidence
  traceability, and evidence-insufficient handling. Silent fallback would make
  the answer support model ambiguous.
- **Alternatives considered**:
  - Hide missing blocks entirely. Rejected because users would not know whether
    support is absent or still loading.
  - Invent precise citations when only document-level support exists. Rejected
    because it violates the product contract.
