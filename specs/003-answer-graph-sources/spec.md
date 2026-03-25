# Feature Specification: Answer Graph And Source Cards

**Feature Branch**: `003-answer-graph-sources`  
**Created**: 2026-03-21  
**Status**: Draft  
**Input**: User description: "In the answer view, change the knowledge visualization into a prettier MiroFish-like graph, and change the source area into a card where each row is one source that points to a specific supporting paragraph in the document."

## Scope Alignment *(mandatory)*

- **Business Requirement Source**: `BUSINESS-REQUIREMENTS.md` sections 1, 5.1, 6.2, 6.3, 6.4, 7.4, 7.5, 7.7, 7.8, 10.1, and 12
- **Current Increment**: Upgrade the answer-result presentation so each answer can show a MiroFish-style small knowledge graph inside the answer unit and present its source evidence as a single card-style list with one row per cited paragraph-level source.
- **Out of Scope**: Changing retrieval or ranking strategy, changing collection selection rules, changing whether web search is enabled, redesigning the full chat page layout, redesigning the full standalone graph page, changing prompt wording beyond what is needed to support paragraph-precise display, and adding new UI modules that were not explicitly requested.
- **Reference Reuse Candidates**: MiroFish graph presentation style for the answer-scoped graph visual treatment, existing fuseAgent/ApeRAG chat answer components for answer rendering, existing fuseAgent graph/detail patterns for reuse where they fit the approved answer context, and existing evidence preview behavior for paragraph inspection.
- **UI Scope**: UI parity-adaptation

## Clarifications

### Session 2026-03-21

- Q: Should this increment only restyle the answer graph and source card, or should graph and evidence support bidirectional linking? -> A: Graph and evidence must support bidirectional linking: clicking a graph node or relation highlights the related evidence rows, and clicking an evidence row focuses or highlights the corresponding graph elements.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Paragraph-Level Sources Inline (Priority: P1)

As an internal user reading an answer, I want the source area to appear as a clear card with one row per cited source paragraph, so I can quickly verify exactly which part of which document supports the answer.

**Why this priority**: The business requirement explicitly defines the product as "answer + evidence + graph," and the evidence must be traceable to original passages. If the source section remains vague or buried, the core trust model of the product is weakened.

**Independent Test**: Ask a question against a knowledge base that has supporting evidence, then verify that the answer shows a source card in the answer result, with each row corresponding to one cited paragraph-level source and identifying the supporting document and passage.

**Acceptance Scenarios**:

1. **Given** an answer has one or more supporting sources, **When** the answer is shown, **Then** the source area appears as a visible card-style list within the answer result rather than only as a detached counter or hidden-only entry point.
2. **Given** an answer cites multiple supporting passages, **When** the source card is rendered, **Then** each cited passage appears as its own row, even if multiple rows come from the same document.
3. **Given** a user scans one source row, **When** the row is displayed, **Then** it clearly identifies the originating document and the specific supporting paragraph or passage used by the answer.
4. **Given** the user wants to inspect a cited source more closely, **When** the user activates a source row, **Then** the product reveals the original supporting passage without forcing the user to leave the current answer context.
5. **Given** the answer result also includes graph data, **When** the user activates a source row, **Then** the answer-scoped graph focuses or highlights the corresponding graph element or relationship linked to that source row.

---

### User Story 2 - Understand the Answer Through a MiroFish-Style Graph (Priority: P2)

As an internal user reading an answer, I want the answer-scoped graph to look and feel like the approved MiroFish graph style, so I can more easily understand the entities and relationships behind the answer instead of seeing a generic or weak placeholder visualization.

**Why this priority**: The business requirement already approved MiroFish as the visual reference for graph-related UI. The user has now explicitly asked for that reference style to be brought into the answer result itself.

**Independent Test**: Ask a question that returns graph-supported knowledge, then verify that the answer result includes a small graph rendered inside the answer unit with a visibly MiroFish-aligned presentation rather than a generic text-only or bare placeholder output.

**Acceptance Scenarios**:

1. **Given** an answer has graph data available, **When** the answer is rendered, **Then** the answer unit includes a visible small graph associated with that answer.
2. **Given** the answer-scoped graph is shown, **When** the user views it, **Then** its visual treatment aligns with the approved MiroFish reference style for graph-related UI rather than defaulting to a generic or unfinished visualization.
3. **Given** the user inspects the graph, **When** the graph is displayed, **Then** the user can distinguish nodes, relationships, and the current focus of the answer without needing to navigate to the full standalone graph page.
4. **Given** the user clicks a graph node or relation, **When** that graph element has supporting evidence rows in the same answer result, **Then** the related evidence rows are highlighted or brought into clear focus.

---

### User Story 3 - Keep Answer, Sources, and Graph in One Cohesive Result (Priority: P3)

As an internal user reading a reply, I want the answer text, the paragraph-level source card, and the small knowledge graph to remain part of the same answer unit, so I can understand the answer, inspect evidence, and see the related graph without context switching.

**Why this priority**: The business requirement states that answer text, evidence, and the related graph should appear as one complete answer, not as disconnected modules. This increment should improve presentation while keeping that unit coherent.

**Independent Test**: Ask a question that yields an answer with evidence and graph data, then verify that the answer body, source card, and graph all appear together in the same answer result and remain understandable even if one supporting block has limited data.

**Acceptance Scenarios**:

1. **Given** an answer includes both evidence and graph data, **When** the answer result is shown, **Then** the answer body, source card, and small graph appear as parts of one coherent answer result.
2. **Given** graph data is unavailable for a specific answer, **When** the answer result is rendered, **Then** the answer body and source card still render correctly and the graph area clearly communicates that graph context is unavailable.
3. **Given** paragraph-precise source support is unavailable for a specific answer segment, **When** the source area is rendered, **Then** the product clearly indicates that exact passage support is unavailable instead of implying a precise citation that does not exist.

### Edge Cases

- What happens when an answer has supporting paragraphs but no graph data?
- What happens when an answer has graph data but only one supporting paragraph?
- What happens when multiple cited rows come from the same document but different paragraphs?
- What happens when the answer has many cited passages and the source card becomes long?
- What happens when the same paragraph is reused for more than one answer claim?
- What happens when a source row has document identity but the exact paragraph mapping cannot be resolved?
- What happens when the answer is marked as evidence-insufficient?
- What happens when a graph block fails to load while the answer text and sources are still available?
- What happens when a graph element maps to multiple evidence rows, or one evidence row maps to multiple graph elements?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each answer result in this increment MUST include an inline answer-scoped graph area when graph data is available for that answer.
- **FR-002**: The inline answer-scoped graph presentation MUST visually align with the approved MiroFish graph style for answer-level graph understanding.
- **FR-003**: The source area in an answer result MUST be presented as a visible card-style source block rather than relying only on a detached counter, hidden drawer trigger, or similarly indirect entry point.
- **FR-004**: The source card MUST present one row per cited supporting paragraph or passage.
- **FR-005**: Every displayed source row MUST identify the originating document and the specific supporting paragraph or passage used by the answer.
- **FR-006**: If multiple supporting passages come from the same document, the system MUST display them as separate source rows when they refer to distinct supporting passages.
- **FR-007**: Users MUST be able to inspect a cited source row's original supporting passage without leaving the current answer context.
- **FR-008**: The answer body, source card, and answer-scoped graph MUST remain part of the same answer result rather than being split into unrelated product areas.
- **FR-009**: Clicking a graph node or relation in the answer-scoped graph MUST highlight or otherwise clearly surface the related source rows in the same answer result.
- **FR-010**: Clicking or activating a source row MUST focus or highlight the corresponding graph element or relationship in the same answer result when graph data exists.
- **FR-011**: If one graph element maps to multiple evidence rows, the system MUST make all related rows visible as linked results rather than implying there is only one supporting row.
- **FR-012**: If one evidence row maps to multiple graph elements or relationships, the system MUST make those linked graph elements discernible in the answer-scoped graph.
- **FR-013**: The answer result in this increment MUST continue to rely only on the selected knowledge base scope for that answer and MUST NOT introduce web-search-based sources when web search is disabled.
- **FR-014**: If graph data is unavailable for an answer, the system MUST present a clear no-graph state without preventing the answer body or source card from rendering.
- **FR-015**: If exact paragraph-level support cannot be resolved for a displayed source candidate, the system MUST clearly indicate that paragraph precision is unavailable instead of presenting an invented precise citation.
- **FR-016**: This increment MUST improve the answer-result presentation only and MUST NOT change the user's collection selection flow, question submission flow, or high-level answer generation flow.
- **FR-017**: This increment MUST preserve the product's Chinese-first presentation behavior.
- **FR-018**: This increment MUST remain aligned with the approved MiroFish graph-related visual reference while avoiding unrelated UI invention outside the requested answer-result blocks.

### Key Entities *(include if feature involves data)*

- **Answer Result**: The single reply unit shown in the conversation, containing the answer body and its supporting presentation blocks.
- **Answer Graph Block**: The small graph visualization attached to one answer result to help users understand the entities and relationships relevant to that specific answer.
- **Source Card**: The answer-level evidence container that lists cited supporting passages as rows.
- **Source Row**: One evidence entry within the source card, representing one cited supporting paragraph or passage from one document.
- **Paragraph Citation**: The traceable reference that points to the exact paragraph or passage used to support the answer.

## Assumptions

- The product already has answer text generation, answer-scoped references, and graph-capable knowledge bases; this increment focuses on upgrading how those answer supports are presented to users.
- Existing evidence preview behavior can be reused as long as the user can inspect a cited passage without leaving the current answer context.
- The answer-scoped graph in this increment is a small graph for the current answer, not a replacement for the full standalone knowledge base graph page.
- This increment may require the answer payload to carry clearer paragraph-level source information, but the user-facing scope remains answer presentation and traceability rather than retrieval-strategy redesign.
- Graph-to-source deep interaction redesign beyond what is needed to show the requested inline graph and source card remains outside this increment.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify at least one supporting paragraph-level source for an answer in under 10 seconds after the answer appears.
- **SC-002**: 100% of displayed source rows include both document identity and paragraph- or passage-level support information.
- **SC-003**: Users can review the answer body, its source card, and its small graph without leaving the current conversation context.
- **SC-004**: Answers that have graph data display an answer-scoped graph as part of the answer result rather than requiring navigation to a separate page to understand the related entities and relationships.
- **SC-005**: In answers where graph data or paragraph-precise source support is unavailable, the product communicates that limitation explicitly rather than implying missing support exists.
- **SC-006**: Users can move from a graph element to its related evidence rows and from an evidence row back to its related graph element without leaving the current answer context.
