# Contract: Trace Graph Display

## Scope

Defines the strict display contract for time mode and entity mode in the answer-support area.

## Time Mode

- Input:
  - `trace_mode = time`
  - non-empty `conclusions`
  - structured graph payload with `layout = timeline`
- Required behavior:
  - Render one gantt main graph.
  - Use event titles derived from real evidence-backed statements.
  - Spread tasks across distinct dates or intervals when evidence supports distinct time positions.
  - Do not render a `graph TD` topology or any secondary grouped cards below the gantt.
- Invalid behavior:
  - all tasks compressed to one day without evidence
  - labels like `时间结论1`, `时间结论2`
  - noisy labels made from URL fragments, import metadata, or raw HTML residue

## Entity Mode

- Input:
  - `trace_mode = entity`
  - graph-ready `@知识库` answer with usable references
- Required behavior:
  - Render a force-layout knowledge-graph subgraph using the same rendering family as the collection knowledge graph.
  - Prefer a non-empty answer-scoped subgraph when related graph elements exist.
  - Keep the result limited to the current answer’s entities and edges.
- Invalid behavior:
  - empty fallback card when related graph elements are available
  - topology/process chart instead of knowledge-graph rendering
  - dumping the entire collection graph without answer scoping
