# Research: Knowledge Base Triple Trace QA

## Decision 1: Reuse knowledge-base purpose as the only extraction guidance signal

- **Decision**: Continue deriving extraction emphasis from the collection's own purpose fields, using `collection.description` and `collection.title` as the only business-intent signal for ontology generation.
- **Rationale**: The clarified spec explicitly rejects a separate global domain intent layer. The current MiroFish graph build path already passes collection purpose text into ontology generation, so this is the smallest compliant extension.
- **Alternatives considered**:
  - Add a hard-coded system-wide military intent. Rejected because it violates FR-021 and makes extraction less reusable across knowledge bases.
  - Add a new runtime intent input for extraction. Rejected because extraction is an indexing concern, not a chat-time concern.

## Decision 2: Split ontology generation into broad fixed base types plus lightweight supplemental types

- **Decision**: Replace the current fully free-form ontology shape with a mixed strategy: a fixed broad base type catalog is always injected first, then the LLM may add lightweight knowledge-base-purpose-driven supplemental entity and relation types up to a higher total cap than the current 10/10 validation limit.
- **Rationale**: The current prompt asks for only 6 to 10 entity types and 4 to 10 relation types, and `_validate_and_process()` truncates results to 10 entity and 10 relation types. That keeps startup light, but it is too narrow for the user's coverage goals. A mixed strategy preserves speed while widening recall.
- **Alternatives considered**:
  - Keep the current fully generated ontology. Rejected because it tends to under-cover broad knowledge bases and can drift too narrow.
  - Use only a fixed ontology with no LLM supplementation. Rejected because it would miss knowledge-base-specific concepts the user wants preserved.

## Decision 3: Keep time and place as evidence-backed attributes on existing entities and relationships

- **Decision**: Do not add an event layer or a fact-unit intermediate model. Instead, enrich the existing entity and relation extraction prompts so time and place remain optional attributes on entities and relations when the source chunk explicitly supports them.
- **Rationale**: `graph_extractor.py` already accepts attribute dictionaries on both entities and relations. This satisfies the clarified spec without changing the graph storage model.
- **Alternatives considered**:
  - Introduce an event node type and rewrite downstream graph logic around it. Rejected because the user explicitly asked not to expand into a separate event-centered model.
  - Infer missing time/place values from neighboring chunks. Rejected because FR-008 forbids inventing unsupported attributes.

## Decision 4: Reuse the existing mixed retrieval path and add mode-specific guidance on top

- **Decision**: Preserve the current default hybrid retrieval pipeline as the base for all answers, and layer trace-mode-specific normalization, filtering, ranking, and organization on top of the same vector, fulltext, and graph evidence channels.
- **Rationale**: `CollectionService.execute_search_flow()` already supports vector, fulltext, and graph search together. The clarified spec requires reuse of the existing path rather than a separate trace-only retriever.
- **Alternatives considered**:
  - Add a dedicated time/space/entity retrieval pipeline. Rejected because it duplicates infrastructure and risks regressing the current default answer quality.
  - Use graph search only for trace modes. Rejected because the current default answer quality also depends on vector and fulltext recall.

## Decision 5: Add an explicit `trace_mode` request control while keeping default mode unchanged

- **Decision**: Extend chat request transport with an optional `trace_mode` value of `default`, `time`, `space`, or `entity`, and keep the absence of that field equivalent to today's default mode behavior.
- **Rationale**: The user wants three new modes without replacing the current answer experience. Adding a small explicit mode control keeps routing clear and backwards-compatible.
- **Alternatives considered**:
  - Infer trace mode only from the natural-language question. Rejected because the user wants an intentional mode switch in the UI.
  - Replace default mode with one trace-aware unified mode. Rejected because FR-001 requires the current default mode to remain available.

## Decision 6: Generate conclusion-level support after the main answer, not inside the streaming path

- **Decision**: Keep the WebSocket answer stream unchanged, then call a post-answer trace-support endpoint that binds major conclusions to existing source rows and prepares the selected trace graph payload.
- **Rationale**: The current answer flow already streams well. A second step avoids destabilizing the main answer path while still delivering conclusion-level citations and mode-specific graph content.
- **Alternatives considered**:
  - Inject conclusion-binding generation into the streaming prompt itself. Rejected because it complicates the streaming contract and mixes answer text with UI support structures.
  - Build citations entirely in the frontend. Rejected because conclusion extraction and source binding need backend access to normalized reference metadata and graph evidence.

## Decision 7: Reuse existing source-row metadata as the citation backbone

- **Decision**: Continue using `tool_reference_extractor.py` output as the authoritative evidence row set, and bind every displayed conclusion to one or more existing `source_row_id` values plus the best trustworthy locator already carried in `Reference.metadata`.
- **Rationale**: The current metadata already includes `source_row_id`, document identity, page hints, chunk IDs, and approximate-vs-precise locator signals. Reusing it minimizes schema churn and keeps displayed citations anchored to real document fragments.
- **Alternatives considered**:
  - Add a parallel citation payload unrelated to source rows. Rejected because it would duplicate evidence identity and make the UI inconsistent.
  - Require exact paragraph coordinates for all citations. Rejected because the current data cannot guarantee that level of precision for every recall path.

## Decision 8: Deliver three clearly different graph organizations by reusing current graph UI foundations

- **Decision**: Keep the current answer-support graph entry points, but generate three distinct mode-specific organizations: a time-ordered graph for time trace, a location-centered grouped graph for space trace, and a focal-entity-centered graph for entity trace.
- **Rationale**: The clarified spec requires visibly different graph structures, not minor highlighting changes. The repo already contains answer-graph service and frontend graph components that can be extended instead of replaced.
- **Alternatives considered**:
  - Reuse one graph layout and change only colors/highlights. Rejected because it does not satisfy FR-018A.
  - Add a completely new graph module disconnected from the current answer support path. Rejected because it creates unnecessary UI churn and deployment risk.

## Decision 9: Treat `web/build` as a required delivery artifact

- **Decision**: Any frontend implementation for this feature must regenerate `web/build` before remote deployment verification.
- **Rationale**: The current frontend Docker image copies `web/build` directly rather than building from `web/src` in the container. Planning without that artifact would be operationally incomplete.
- **Alternatives considered**:
  - Rely on remote container build from source. Rejected because the active Dockerfile does not do that.
  - Skip deployment verification and validate only local source changes. Rejected because the constitution requires real runnable verification for behavior-changing features.
