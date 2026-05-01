# Implementation Plan: Knowledge Base Triple Trace QA

**Branch**: `013-triple-trace-qa` | **Date**: 2026-04-03 | **Spec**: [spec.md](E:/codes/fuseAgent_v2/fuseAgent/specs/013-triple-trace-qa/spec.md)  
**Input**: Feature specification from [spec.md](E:/codes/fuseAgent_v2/fuseAgent/specs/013-triple-trace-qa/spec.md)

## Summary

Preserve the current default knowledge-base QA path and add three selectable
trace modes for time, space, and entity views by extending, not replacing, the
current stack. The implementation will strengthen ontology generation with a
fixed broad base type catalog plus lightweight knowledge-base-purpose-driven
supplemental types, preserve evidence-backed time/place attributes on extracted
entities and relationships, reuse the current mixed retrieval path
(`vector + fulltext + graph`) for all modes, add a post-answer trace-support
step for conclusion-level citations, and present three clearly different
mode-specific graphs.

## Technical Context

**Language/Version**: Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend  
**Primary Dependencies**: FastAPI, Pydantic, SQLAlchemy-backed services, existing WebSocket chat flow, existing collection search flow, existing MiroFish graph extraction stack, existing answer graph service, Next.js 15, next-intl, Tailwind CSS 4, `react-force-graph-2d`, Mermaid  
**Storage**: PostgreSQL metadata, existing vector store, Elasticsearch fulltext index, LightRAG graph/search artifacts, Neo4j-backed MiroFish graph data, existing reference metadata carried in `Reference.metadata`  
**Testing**: Targeted `pytest`, `corepack yarn lint`, `corepack yarn build`, and local/remote browser smoke validation for chat mode selection, citations, and graphs  
**Target Platform**: Linux-hosted full-stack web app with Windows development workspace and remote deployment via Docker Compose  
**Project Type**: Full-stack web application  
**Performance Goals**: Preserve current default answer quality and streaming behavior, keep ontology startup guidance lightweight, avoid introducing a separate heavy trace retrieval pipeline, keep post-answer trace support fast enough to render shortly after the main answer completes, and keep full acceptance indexing for `E:\codes\fuseAgent_v2\iw_docs` within 4 minutes  
**Constraints**: Keep default mode unchanged, no global system intent layer, no event/fact-unit intermediate model, reuse current mixed retrieval channels, preserve Chinese-first behavior, bind conclusions only to real source rows, regenerate `web/build` because the active frontend Docker image copies built artifacts rather than source, and satisfy the collection graph thresholds of >80 nodes and >100 edges on the acceptance dataset  
**Scale/Scope**: Knowledge-base chat input, answer support, ontology generation, extraction prompts, answer-level citations, and answer-level graph presentation for internal single-knowledge-base QA

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Acceptance plan identifies whether this feature must import all documents from `E:\codes\fuseAgent_v2\iw_docs`, and this increment requires that recurring full-dataset validation.
- [x] Validation plan states the required graph quality thresholds when graph behavior changes: rendered collection graph, node count > 80, edge count > 100.
- [x] The QA mode plan names the required output contract for default, time, entity, and space trace behavior, including the single-location focus plus location-specific gantt view.
- [x] If UI behavior changes, this feature treats `ui-satisfied-graph-workbench` as the approved UI baseline and any continued UI work must stay isolated from that correct branch.
- [x] Post-implement validation includes service restart details for the changed backend/frontend stack and confirms reachable frontend/API verification paths after deployment.
- [x] Remote verification names the server startup path, local port-forward target, and automated acceptance path used for final sign-off.

## Phase 0 Research

See [research.md](E:/codes/fuseAgent_v2/fuseAgent/specs/013-triple-trace-qa/research.md) for the implementation decisions that resolve the main design questions. The key conclusions are:

1. Use knowledge-base purpose from collection metadata as the only extraction guidance signal; do not add a global system intent layer.
2. Replace the narrow fully free-form ontology path with a mixed base-plus-supplemental type strategy and raise the effective type ceiling beyond the current 10/10 clamp.
3. Keep time/place as optional evidence-backed attributes on existing entities and relationships instead of introducing an event model or an intermediate fact layer.
4. Reuse the current mixed retrieval path for default and trace modes, then add mode-specific normalization, ranking, and organization.
5. Keep the main answer stream unchanged and compute conclusion bindings plus trace graphs in a post-answer trace-support step.
6. Reuse existing `source_row_id`-based reference metadata as the citation backbone.
7. Deliver three visually distinct graph organizations for time, space, and entity modes.
8. Treat `web/build` regeneration as part of the required delivery path.

## Phase 1 Design

### Data Model

See [data-model.md](E:/codes/fuseAgent_v2/fuseAgent/specs/013-triple-trace-qa/data-model.md). The increment centers on:

- Knowledge base purpose signal
- Ontology profile
- Traceable attribute set
- Extracted entity
- Extracted relationship
- Trace mode
- Trace retrieval context
- Major conclusion binding
- Trace graph payload
- Trace support response

### Interface Contracts

See [chat-trace-mode.md](E:/codes/fuseAgent_v2/fuseAgent/specs/013-triple-trace-qa/contracts/chat-trace-mode.md), [reference-metadata.md](E:/codes/fuseAgent_v2/fuseAgent/specs/013-triple-trace-qa/contracts/reference-metadata.md), and [trace-support.md](E:/codes/fuseAgent_v2/fuseAgent/specs/013-triple-trace-qa/contracts/trace-support.md).

### Quickstart

See [quickstart.md](E:/codes/fuseAgent_v2/fuseAgent/specs/013-triple-trace-qa/quickstart.md) for the validation flow implementation must pass.

## Project Structure

### Documentation (this feature)

```text
specs/013-triple-trace-qa/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- chat-trace-mode.md
|   |-- reference-metadata.md
|   `-- trace-support.md
`-- tasks.md
```

### Source Code (repository root)

```text
aperag/
|-- agent/
|   `-- tool_reference_extractor.py
|-- mcp/
|   `-- server.py
|-- mirofish_graph/
|   |-- ontology_generator.py
|   `-- graph_extractor.py
|-- schema/
|   `-- view_models.py
|-- service/
|   |-- agent_chat_service.py
|   |-- answer_graph_service.py
|   |-- collection_service.py
|   |-- mirofish_graph_service.py
|   `-- prompt_template_service.py
`-- views/
    `-- collections.py

tests/
`-- unit_test/
    |-- agent/
    |-- mirofish_graph/
    `-- service/

web/
|-- build/
`-- src/
    |-- api/
    |   `-- models/
    |-- app/
    |   `-- workspace/
    `-- components/
        `-- chat/
            |-- chat-input.tsx
            |-- chat-messages.tsx
            |-- message-answer-graph.tsx
            |-- message-answer-support.tsx
            |-- message-answer-support.types.ts
            |-- message-parts-ai.tsx
            `-- message-reference.tsx
```

**Structure Decision**: Keep the existing backend/frontend layout and extend the
current chat, graph, and extraction modules in place. Avoid any new top-level
feature module or separate trace-only subsystem.

## Implementation Strategy

### Phase 1: Ontology And Extraction Enhancement

- Update `aperag/mirofish_graph/ontology_generator.py` so the ontology prompt always injects a fixed broad base type catalog, then asks the LLM for lightweight knowledge-base-purpose-driven supplemental types.
- Raise the final accepted ontology ceiling beyond the current 10 entity / 10 relation truncation while keeping validation bounded and deduplicated.
- Revise the ontology prompt wording so time/place-bearing types and broad coverage are explicitly encouraged without requiring a heavy all-document pass beyond the current input budget.
- Update `aperag/mirofish_graph/graph_extractor.py` extraction guidance so entities and relationships retain explicit time/place attributes only when the source chunk supports them.
- Keep `aperag/service/mirofish_graph_service.py` on the current collection-purpose signal path and avoid introducing any global system intent field.

### Phase 2: Default Plus Triple-Trace Mixed Retrieval

- Extend `aperag/schema/view_models.py`, `aperag/service/agent_chat_service.py`, and generated frontend API models so chat requests can carry `trace_mode`.
- Add mode-aware prompt guidance in `aperag/service/prompt_template_service.py` so default mode keeps current behavior while time/space/entity modes normalize user intent for retrieval and answer organization.
- Reuse `aperag/service/collection_service.py` mixed retrieval execution for all modes, ensuring vector, fulltext, and graph recall remain available.
- Implement trace-mode-specific normalization helpers:
  - `time`: convert natural-language dates/periods into normalized time windows for ranking
  - `space`: normalize place names and aliases for ranking and grouping
  - `entity`: normalize focal entity names and disambiguation hints for ranking and grouping
- Keep fallback behavior explicit when structured evidence for the selected dimension is incomplete.

### Phase 3: Conclusion Binding And Trace Support Backend

- Add a new collection-scoped trace-support endpoint in `aperag/views/collections.py` backed by a service that runs after the main answer completes.
- Reuse `tool_reference_extractor.py` output and `Reference.metadata` as the evidence identity layer so every conclusion binds to existing `source_row_id` values.
- Generate a concise set of answer-level major conclusions, each with bound source rows and locator quality metadata.
- Reuse or extend `aperag/service/answer_graph_service.py` so the same evidence package can also produce a trace-mode graph payload instead of inventing a second unrelated graph backend.
- Keep default-mode support available so the new backend path can also provide conclusion-level citations for the current answer mode.

### Phase 4: Mode-Specific Graphs And Answer UI

- Treat `ui-satisfied-graph-workbench` as the approved UI baseline for graph/workbench-related visuals and interactions; any further UI adjustments for this increment must be isolated in a new working branch or equivalent isolated workspace rather than changing that baseline branch directly.
- Add a mode selector to the existing chat input action area without disturbing current submit and mention flows.
- Update the answer-support UI so it can request and render trace-support results after the main answer arrives.
- Keep the current source drawer/reference UI as the evidence surface and overlay conclusion-level citation markers that point into the same source-row set.
- Extend the current graph components to render three meaningfully different organizations:
  - `time`: ordered timeline-like or period-grouped graph
  - `space`: one focal location plus a time-ordered gantt-style view containing only events tied to that location
  - `entity`: focal-entity-centered subgraph
- Keep default mode presentation intact while allowing the three trace modes to show their own graph organization and citation framing.

### Phase 5: Validation, Build Artifacts, And Runtime Restart

- Add targeted backend tests for ontology profile generation, attribute retention, trace-mode request parsing, trace-support conclusion binding, and approximate-vs-precise citation labeling.
- Add frontend checks for mode selection transport, conclusion citation rendering, and graph mode switching.
- Import the full acceptance dataset from `E:\codes\fuseAgent_v2\iw_docs` into a fresh knowledge base, verify all required indexes finish within 4 minutes, and treat any overrun as a failed sign-off.
- Verify the collection graph page renders successfully on the acceptance knowledge base and satisfies the minimum graph size thresholds of >80 nodes and >100 edges.
- Verify:
  - `default`: text + visible citations + topology/process graph + source list
  - `time`: default artifacts + day-level gantt when evidence supports it
  - `space`: default artifacts + one focal location + location-specific time-ordered gantt
  - `entity`: default artifacts + answer-scoped entity/edge subgraph
- Regenerate `web/build` after frontend changes because the deployment image copies the built output directly.
- Restart the changed stack with the real remote deployment flow defined in `docker-compose.deploy.remote.yml`, then verify the forwarded frontend and API endpoints remain reachable.
- Record any residual limitations where trace organization falls back to weaker evidence because source material lacks explicit time/place/entity structure.

## Post-Design Constitution Check

- [x] The design remains confined to knowledge-base QA and does not add a system-wide intent layer or an event/fact-unit subsystem.
- [x] Reuse still dominates: current extraction flow, current mixed retrieval path, current reference metadata, and current answer graph UI are all extended rather than replaced.
- [x] UI scope remains within the approved chat input, answer support, citation, and graph surfaces.
- [x] The UI baseline branch rule is respected: future graph/workbench UI work is defined relative to `ui-satisfied-graph-workbench`, but is not allowed to pollute that branch directly.
- [x] Real deployment constraints are addressed explicitly, including `web/build` regeneration, remote startup, local port-forwarding, and recurring `iw_docs` validation.
- [x] The feature keeps Chinese-first behavior and preserves the current default mode as a first-class path while defining the fixed-location gantt requirement for space trace.

## Complexity Tracking

No constitution violations require justification for this increment.
