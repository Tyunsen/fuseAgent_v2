# Research: Trace Graph Citations

## Decision 1: Finish The Existing Trace-Support Path Instead Of Forking It

- **Decision**: Keep fixing the current `trace_support_service -> answer_graph_service -> message-answer-support` path.
- **Rationale**: The product already has the right surfaces for triple-trace QA. The failures are contract failures inside an existing path, not evidence that the architecture is wrong.
- **Alternatives considered**:
  - Build a separate trace-mode backend DTO and frontend renderer: rejected because it duplicates the current graph/evidence pipeline and increases drift risk.
  - Let the LLM emit final display graphs directly: rejected because the existing bugs already show prompt-only rendering is too unstable.

## Decision 2: Inline Citations Must Be Interactive Rendered Anchors

- **Decision**: Keep citation numbering derived from prepared reference rows, then render `[n]` as clickable inline controls in the answer body.
- **Rationale**: Reference-row order already defines stable answer-local evidence numbering. Turning those tokens into interactive UI is cheaper and more reliable than inventing a new persistence schema.
- **Alternatives considered**:
  - Persist citation numbers in message history: rejected because the feature only needs stable per-answer numbering at render time.
  - Continue rendering plain-text `[n]`: rejected because the user requires click-to-open drawer behavior.

## Decision 3: Remove Detached Citation Buttons Entirely

- **Decision**: Delete the top-right citation-number strip from the answer card header.
- **Rationale**: It violates the contract that citations must appear at the actual cited sentence and makes the message shell look like a duplicate evidence widget.
- **Alternatives considered**:
  - Keep the strip as a secondary shortcut: rejected because the user explicitly considers it wrong and misleading.
  - Move the strip elsewhere in the card: rejected because the contract is not “move it”, but “render citations inline”.

## Decision 4: Backend Owns Event Title Cleaning For Time Gantt

- **Decision**: Extract cleaner event titles and better time labels in `trace_support_service.py`; keep the frontend focused on safe display truncation and Mermaid generation.
- **Rationale**: The noisy gantt labels originate from evidence-row fallback text. Fixing the upstream statement/title derivation gives both Mermaid and other consumers cleaner data.
- **Alternatives considered**:
  - Clean labels only in the frontend: rejected because it treats symptoms and still leaves bad structured conclusions in the payload.
  - Ask the LLM to always provide perfect gantt labels: rejected because it does not solve fallback rows and deterministic rendering cases.

## Decision 5: Entity Mode Needs Progressive Matching Before Empty Fallback

- **Decision**: When direct row-to-graph mapping is sparse, widen matching using current-answer row context, linked chunk ids, and answer focus terms before declaring the graph empty.
- **Rationale**: The user is querying graph-ready collections that already contain large numbers of nodes and edges. Empty entity graphs in that context are usually a matching failure, not a genuine lack of relevant graph elements.
- **Alternatives considered**:
  - Return the full collection graph when exact mapping fails: rejected because entity mode must stay answer-scoped.
  - Keep the current exact-only linking: rejected because it already fails on real graph-ready collections.

## Decision 6: Remote Frontend Deployment Must Include `web/build`

- **Decision**: Treat regenerated `web/build` as part of the deploy artifact whenever chat UI behavior changes.
- **Rationale**: The remote frontend image is built from the `web` Docker context and copies `web/build`. Shipping only source files can leave runtime UI stale even when the worktree is correct.
- **Alternatives considered**:
  - Sync only changed source files and rely on remote build later: rejected because it already produced stale runtime results during earlier verification.
