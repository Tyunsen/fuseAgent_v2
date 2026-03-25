# Research: ApeRAG Answer Topology And Sources

## Decision 1: Restore the ApeRAG answer interaction instead of extending `MessageAnswerSupport`

- **Decision**: Remove the inline `MessageAnswerSupport` block from the active answer rendering path and reuse the existing `MessageReference` drawer entry in the answer footer.
- **Rationale**: The user explicitly rejected the extra `Knowledge Graph` module and asked to keep the ApeRAG structure. Reusing `MessageReference` is the smallest change that restores that behavior.
- **Alternatives considered**:
  - Keep the inline support block and only hide the graph section. Rejected because it still changes the answer structure more than approved.
  - Keep both the inline block and the drawer. Rejected because it duplicates sources and adds UI the user did not ask for.

## Decision 2: Keep Mermaid as the topology source of truth

- **Decision**: Continue rendering `流程拓扑` from the existing Mermaid markdown content and improve only the `ChartMermaid` presentation shell.
- **Rationale**: The user explicitly asked to keep ApeRAG's original graph generation and only change the rendering effect toward MiroFish.
- **Alternatives considered**:
  - Replace Mermaid with a new graph data pipeline. Rejected because it changes generation logic rather than rendering only.
  - Add a second graph block next to Mermaid. Rejected because it creates a new UI module the user rejected.

## Decision 3: Use the existing reference payload with better row shaping

- **Decision**: Build source rows from existing `Reference.metadata` and passage text, adding better content cleanup and locator extraction in the frontend helper layer plus a small extractor cleanup for preview titles.
- **Rationale**: This stays inside the approved presentation scope and avoids adding new backend endpoints or payload formats for a drawer-only change.
- **Alternatives considered**:
  - Add a new answer-source API. Rejected because it adds architecture and risk not required by the feature.
  - Show raw reference text directly. Rejected because it fails the user's request for clearer per-row paragraph/source inspection.

## Decision 4: Prefer trustworthy approximate locators over invented precision

- **Decision**: Use page, heading, or other trustworthy source hints when exact paragraph coordinates are unavailable, and clearly mark the locator as approximate.
- **Rationale**: This aligns with the business requirement for traceable evidence without fabricating unsupported exactness.
- **Alternatives considered**:
  - Omit locators when exact paragraph metadata is missing. Rejected because it makes the source rows too vague.
  - Infer fake paragraph numbers from UI order. Rejected because it is not trustworthy.
