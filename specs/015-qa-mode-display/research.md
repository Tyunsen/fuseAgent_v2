# Research: QA Mode Display

## Decision 1: Keep Existing Streaming Transport

- **Decision**: Reuse the current WebSocket streaming path and message chunking behavior.
- **Rationale**: The existing path already streams assistant message chunks incrementally and was previously acceptance-tested; 015 only needs to preserve and verify that behavior, not redesign transport.
- **Alternatives considered**:
  - Replace with a new SSE-only transport: rejected because it would broaden scope and risk regressions outside the feature.
  - Force client-side fake streaming from complete text: rejected because it would degrade true incremental delivery.

## Decision 2: Collapse Sources Into One Unified Evidence Surface

- **Decision**: Keep inline references plus one collapsed source list panel, and remove duplicate standalone source cards in answer support.
- **Rationale**: The current UI duplicates evidence in multiple places, which clashes with the requested minimal answer shell.
- **Alternatives considered**:
  - Keep both drawer sources and card sources: rejected because it preserves the exact duplication the feature is meant to remove.
  - Remove expandable source list entirely: rejected because the user explicitly requires a collapsible list.

## Decision 3: Entity Mode Must Reuse Knowledge Graph Rendering

- **Decision**: Entity mode should render with the existing force-graph / knowledge-graph component path instead of Mermaid.
- **Rationale**: The user explicitly wants a different rendering style and reuse of the knowledge graph presentation already present in the product.
- **Alternatives considered**:
  - Mermaid subgraph: rejected because it does not satisfy the requested rendering style.
  - Build a completely new graph renderer: rejected because reuse is sufficient and lower risk.

## Decision 4: Space Mode Reverts To Default Topology Shell

- **Decision**: Space mode now shares the default shell and uses `graph TD`.
- **Rationale**: The constitution was updated to match the user's new preference, so planning and implementation must follow that latest governance.
- **Alternatives considered**:
  - Keep location-specific gantt: rejected because it conflicts with the current constitution and the latest user direction.

## Decision 5: Document-Level Graph Status Stays Visible While Source Of Truth Remains Collection-Level

- **Decision**: Show document-level graph status in the UI, but treat collection graph state as the authoritative signal for whether polling should continue.
- **Rationale**: This satisfies the user's need for per-document visibility without changing backend graph lifecycle ownership.
- **Alternatives considered**:
  - Hide document-level status and show collection-only state: rejected because the user explicitly does not want that.
  - Move graph lifecycle to truly per-document backend indexing: rejected because it is out of scope and unnecessary for the requested UX.

## Decision 6: Poll Document Page Every 15 Seconds Only During Active Build

- **Decision**: Add a client-side 15-second refresh loop only when the collection graph status is `building` or `updating`.
- **Rationale**: This is the smallest implementation that meets the requirement while avoiding continuous refresh after stabilization.
- **Alternatives considered**:
  - Faster polling (e.g. 3-5 seconds): rejected because it creates more load without being requested.
  - Permanent polling: rejected because the user explicitly wants polling to stop after build completion.
