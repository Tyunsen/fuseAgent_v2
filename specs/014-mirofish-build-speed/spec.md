# Feature Specification: MiroFish Build Speed Recovery

**Feature Branch**: `014-mirofish-build-speed`  
**Created**: 2026-04-03  
**Status**: Draft  
**Input**: User description: "MiroFish native can reach this speed level. Continue optimizing so the recurring acceptance dataset can finish full indexing within the required time budget without regressing graph quality or approved QA behavior."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Full Knowledge Base Ready Within Budget (Priority: P1)

As a project owner, I want the full acceptance knowledge base built from the recurring validation dataset to finish vector, fulltext, and graph indexing within the agreed time budget, so I can trust that the product is ready for recurring end-to-end acceptance rather than only small smoke tests.

**Why this priority**: The current hard blocker is that the recurring acceptance dataset does not finish full indexing within the required time window. Until this is fixed, the feature set cannot pass the project constitution.

**Independent Test**: Import every document from `E:\codes\fuseAgent_v2\iw_docs` into a fresh knowledge base on the remote acceptance environment and verify that vector, fulltext, and graph indexing all become available within 4 minutes.

**Acceptance Scenarios**:

1. **Given** a fresh knowledge base is created from the recurring acceptance dataset, **When** the full import starts, **Then** vector, fulltext, and graph indexing complete within 4 minutes.
2. **Given** the acceptance dataset contains mixed document formats, **When** the build completes, **Then** no document that belongs to the accepted dataset is silently omitted from the knowledge base.
3. **Given** the graph build completes, **When** the collection status is inspected, **Then** the graph is marked ready with an active graph identifier instead of remaining stuck in building or failed state.

---

### User Story 2 - Graph Workbench Stays Correct (Priority: P1)

As an analyst using the graph workbench, I want the accepted graph page to keep rendering correctly after the speed optimization, so that performance work does not damage the approved graph browsing experience.

**Why this priority**: Faster indexing is not useful if it degrades the graph workbench that has already been treated as the accepted UI baseline.

**Independent Test**: Open the collection graph page for the acceptance knowledge base after indexing finishes and verify that the graph renders successfully with more than 80 nodes and more than 100 relationships.

**Acceptance Scenarios**:

1. **Given** the acceptance knowledge base has finished indexing, **When** the graph workbench page opens, **Then** the graph renders successfully without empty placeholders or graph API validation failures.
2. **Given** the graph workbench page renders, **When** the graph data is counted, **Then** the rendered graph contains more than 80 nodes and more than 100 relationships.
3. **Given** the graph workbench UI has already been accepted, **When** speed improvements are delivered, **Then** the accepted interaction and visual direction remain recognizable rather than being replaced by an unrelated graph UI.

---

### User Story 3 - Answer Modes Keep Their Contracts (Priority: P2)

As an analyst using default, time, space, and entity QA modes, I want the approved answer-mode behavior to remain correct after speed optimization, so performance gains do not come at the cost of answer quality, citations, or mode-specific visuals.

**Why this priority**: The system is not accepted by speed alone; it must also preserve the agreed answer contracts across all four modes.

**Independent Test**: After the acceptance knowledge base becomes ready, ask representative questions in default, time, space, and entity modes and verify that each mode still produces its required answer artifacts.

**Acceptance Scenarios**:

1. **Given** the user asks in default mode, **When** the answer is returned, **Then** the result includes answer text, visible citations, a topology or process graph, and a source list.
2. **Given** the user asks in time mode, **When** the answer is returned, **Then** the result includes the default-mode artifacts plus a time gantt view with day-level precision whenever the evidence supports day-level dates.
3. **Given** the user asks in space mode, **When** the answer is returned, **Then** the result includes the default-mode artifacts plus one focal location and a time-ordered gantt view containing only the events tied to that location.
4. **Given** the user asks in entity mode, **When** the answer is returned, **Then** the result includes the default-mode artifacts plus an answer-scoped subgraph containing only the entities and relationships used by the current answer.
5. **Given** the graph has been built successfully, **When** answer support is requested, **Then** the support view uses real graph data rather than incorrectly falling back to a temporary unavailable message.

### Edge Cases

- What happens when a few large source files slow down the overall acceptance build even though smaller files complete quickly?
- What happens when graph generation succeeds for most of the dataset but one late-stage graph task leaves the collection stuck in building state?
- What happens when the graph is marked ready but answer-support graph mapping still fails because the returned graph payload violates the expected schema?
- What happens when the accepted dataset includes file formats that need normalization before they can participate in the recurring acceptance build?
- What happens when speed improvements accidentally reduce graph density and the graph page renders with too few nodes or relationships?
- What happens when the remote services restart successfully but local port forwarding or automated acceptance still fails?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support recurring end-to-end acceptance using the full document set under `E:\codes\fuseAgent_v2\iw_docs`.
- **FR-002**: The recurring acceptance build MUST finish vector, fulltext, and graph indexing for the full acceptance dataset within 4 minutes.
- **FR-003**: The recurring acceptance build MUST produce a collection-level graph that reaches ready state with an active graph identifier.
- **FR-004**: The recurring acceptance process MUST include every document in the accepted dataset, including files that require normalization before import.
- **FR-005**: The collection graph page MUST render successfully for the acceptance knowledge base after the graph becomes ready.
- **FR-006**: The rendered collection graph for the acceptance knowledge base MUST contain more than 80 nodes and more than 100 relationships.
- **FR-007**: The accepted graph workbench experience MUST remain aligned with the currently accepted UI baseline instead of being replaced by a new unrelated UI direction.
- **FR-008**: Default QA mode MUST continue to return answer text, visible citations, a topology or process graph, and a source list after the speed optimization.
- **FR-009**: Time QA mode MUST continue to return the default-mode artifacts plus a time gantt view with day-level precision whenever the source evidence supports exact days.
- **FR-010**: Space QA mode MUST continue to return the default-mode artifacts plus one focal location and a time-ordered gantt view containing only events tied to that focal location.
- **FR-011**: Entity QA mode MUST continue to return the default-mode artifacts plus an answer-scoped knowledge subgraph containing only the entities and relationships used in the current answer.
- **FR-012**: When the collection-level graph is ready, answer-support and trace-support graph views MUST use the available graph data rather than incorrectly falling back to a graph unavailable state.
- **FR-013**: Each implementation pass for this feature MUST restart the remote service stack, forward ports to the local machine, and run automated acceptance against the forwarded URLs.
- **FR-014**: The optimization work MUST NOT weaken graph quality, citation traceability, or the approved answer-mode contracts in order to reach the speed target.

### Key Entities *(include if feature involves data)*

- **Acceptance Dataset**: The recurring full document set located at `E:\codes\fuseAgent_v2\iw_docs` that defines the required end-to-end validation workload.
- **Acceptance Knowledge Base**: A freshly created knowledge base populated from the full acceptance dataset and used to measure indexing speed, graph readiness, and answer-mode correctness.
- **Collection-Level Graph Status**: The graph lifecycle state and active graph identifier that show whether the knowledge base graph is truly ready for graph search and answer-support use.
- **Graph Workbench Result**: The rendered graph page output for the acceptance knowledge base, including node count, relationship count, and visible usability state.
- **Mode Contract Result**: The validated output package for one QA mode, including answer text, citations, and any required graph or gantt visualization.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of recurring acceptance runs that are marked successful finish vector, fulltext, and graph indexing for the full `iw_docs` dataset within 4 minutes.
- **SC-002**: 100% of successful recurring acceptance runs produce a collection graph that reaches ready state with a non-empty active graph identifier.
- **SC-003**: 100% of successful recurring acceptance runs render the collection graph page without an empty placeholder or graph API validation failure.
- **SC-004**: On successful recurring acceptance runs, the collection graph contains more than 80 nodes and more than 100 relationships.
- **SC-005**: 100% of validated default-mode answers include answer text, visible citations, a topology or process graph, and a source list.
- **SC-006**: 100% of validated time-mode answers include a gantt view, and when source evidence includes exact dates, the gantt uses day-level precision.
- **SC-007**: 100% of validated space-mode answers lock onto one focal location and show a gantt view containing only the events tied to that location.
- **SC-008**: 100% of validated entity-mode answers include a subgraph limited to the entities and relationships used by the answer itself.
- **SC-009**: 100% of successful recurring acceptance runs can be reproduced on the remote environment through restarted services and locally forwarded verification URLs.

## Assumptions

- The current project constitution defines the acceptance dataset, speed budget, graph thresholds, and four-mode answer contracts as recurring mandatory gates for every completed feature.
- The existing MiroFish-based graph pipeline has enough optimization headroom to reach the required speed target without removing graph content or answer-mode behavior.
- The currently accepted graph workbench UI remains the visual and interaction baseline that optimization work should preserve.
- The remote environment remains the authoritative place for final acceptance, even if local development checks pass earlier.
- Some dataset files may require format-preserving normalization before import, but their information content must still participate in the acceptance build.
