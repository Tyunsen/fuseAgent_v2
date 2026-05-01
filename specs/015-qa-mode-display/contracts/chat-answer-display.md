# Contract: Chat Answer Display

## Scope

Defines the required frontend-visible answer shell for knowledge-base QA across default, time, space, and entity modes.

## Contract

1. Every mode MUST keep streaming answer text when the backend emits incremental message chunks.
2. Every mode MUST show visible inline citation markers whenever source-backed content is present.
3. Every mode MUST expose one unified source list titled “本次回答文档来源” (or equivalent localized copy).
4. The unified source list MUST be collapsed by default and user-expandable.
5. Default mode MUST NOT render separate trace summary, key conclusions, or standalone source cards.
6. Time mode MUST keep the same minimal shell as default mode while rendering a gantt chart as the main graph.
7. Space mode MUST keep the same minimal shell as default mode while rendering the same `graph TD` topology graph as the main graph.
8. Entity mode MUST render its main graph with the existing knowledge-graph renderer, not Mermaid.
9. Entity mode MUST NOT render an extra “Knowledge Graph 回答关联图谱” support card outside the main graph region.
