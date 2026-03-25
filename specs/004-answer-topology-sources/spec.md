# Feature Specification: ApeRAG Answer Topology And Sources

**Feature Branch**: `004-answer-topology-sources`  
**Created**: 2026-03-22  
**Status**: Draft  
**Input**: User description: "$speckit-specify 回退到003-answer-graph-sources动工之前的代码，然后实现以下的： 1.我是说【知识图可视化】的【流程拓扑】的那个图，变成mirofish一样好看的渲染效果。不是叫你新加什么【Knowledge Graph】。aperag本来是怎么生成那些图的，你就保存呗，只不过展示的时候是mirofish的渲染效果 2.来源变成一行一行，精确到文档的哪一段。可以弄一个来源的折叠卡片。尽量保持aperag的原来样式 3.尽可能保存aperag的原来样式，不要乱变其他的"

## Scope Alignment *(mandatory)*

- **Business Requirement Source**: `BUSINESS-REQUIREMENTS.md` sections 1, 3, 4.3, 6.2, 6.3, 6.4, 7.4, 7.5, 7.7, 8.1, 8.2, 10.1, and 12
- **Current Increment**: Restore the answer page to the pre-`003-answer-graph-sources` interaction structure, then improve only two answer-support surfaces within that existing structure: the existing `流程拓扑` graph render and the source-reference presentation.
- **Out of Scope**: Adding a new standalone answer-scoped `Knowledge Graph` module, changing retrieval logic, changing graph generation logic, changing source ranking logic, redesigning the full chat page, changing the conversation flow, or adding unrelated visual redesign outside the existing ApeRAG answer and source areas.
- **Reference Reuse Candidates**: Existing ApeRAG answer layout and source-entry pattern for the base interaction structure, existing ApeRAG-generated topology content as the graph source, and MiroFish graph visual treatment as the rendering reference only.
- **UI Scope**: UI parity-adaptation

## Clarifications

### Session 2026-03-22

- Q: Should the source presentation keep the original ApeRAG source entry and drawer behavior, or move sources inline under the answer? -> A: Keep the original ApeRAG source entry and drawer behavior, and only change the drawer content into a one-row-per-source collapsible card list.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Keep ApeRAG Answer Structure (Priority: P1)

As an internal user reading an answer, I want the answer page to stay close to the original ApeRAG structure instead of introducing a new extra answer graph module, so I can continue using the familiar workflow while getting better visuals and clearer evidence.

**Why this priority**: The user explicitly rejected the added `Knowledge Graph` block and asked to return to the earlier ApeRAG-style answer structure before improving the requested surfaces.

**Independent Test**: Open a chat answer that includes topology content and references, then verify that the answer page does not include a new extra graph block beyond the existing ApeRAG answer structure.

**Acceptance Scenarios**:

1. **Given** an answer contains the existing ApeRAG topology content, **When** the answer is rendered, **Then** the product uses the existing answer structure rather than introducing a separate new answer graph module.
2. **Given** the answer page includes source references, **When** the user views the answer footer or source entry area, **Then** the interaction stays close to the original ApeRAG pattern instead of replacing the page with a new custom support layout.
3. **Given** the answer has sources, **When** the user opens them, **Then** the user enters the existing ApeRAG-style source drawer rather than a new inline answer block.

---

### User Story 2 - View a Better-Looking Existing Topology (Priority: P1)

As an internal user reading an answer, I want the existing `流程拓扑` graph to look like a refined MiroFish-style render while still representing the same underlying generated topology content, so I can understand the answer context more clearly without changing what the system generated.

**Why this priority**: The graph should help users understand the answer, but the user only approved a rendering upgrade, not a new graph-generation workflow or a new graph module.

**Independent Test**: Open an answer that already includes a `流程拓扑` graph and verify that the graph content remains the same while the visual rendering is upgraded toward the approved MiroFish reference style.

**Acceptance Scenarios**:

1. **Given** an answer includes `流程拓扑` content, **When** it is rendered, **Then** the system continues to use the same underlying topology content source that ApeRAG already generated.
2. **Given** the existing topology is shown, **When** the user views it, **Then** the rendering quality is visually closer to the approved MiroFish graph style than the default plain render.
3. **Given** the topology cannot be rendered successfully, **When** the answer is displayed, **Then** the user can still access the original topology data representation without losing the answer itself.

---

### User Story 3 - Inspect Sources Row by Row (Priority: P2)

As an internal user reading an answer, I want the sources to appear as a row-by-row collapsible card list that points to the supporting part of the document, so I can verify which paragraph or passage supports the answer without leaving the current context.

**Why this priority**: The business requirement depends on trustable paragraph-level evidence, and the user asked for a clearer but still ApeRAG-like source presentation.

**Independent Test**: Open an answer with multiple references, then verify that the source panel shows one row per source passage, each row can be expanded, and each row identifies the document and the supporting location.

**Acceptance Scenarios**:

1. **Given** an answer has multiple supporting references, **When** the user opens the source panel, **Then** the system shows one row per supporting source passage rather than one undifferentiated block.
2. **Given** a source row is shown, **When** the user scans it, **Then** the row identifies the source document and the supporting location using page, title, paragraph, or a clearly stated approximate locator.
3. **Given** a user needs more detail, **When** the user expands a source row, **Then** the system reveals the supporting passage inside the current source panel rather than forcing navigation away from the answer.
4. **Given** exact paragraph precision is unavailable for a source, **When** the row is displayed, **Then** the system clearly indicates that the locator is approximate instead of pretending it is exact.
5. **Given** the user opens the sources for an answer, **When** the source UI appears, **Then** it uses the existing ApeRAG drawer-style entry pattern with upgraded row content inside the drawer.

### Edge Cases

- What happens when an answer includes the existing topology content but the visual renderer fails?
- What happens when a source has document identity and page information but no exact paragraph locator?
- What happens when multiple source rows come from the same document but different supporting passages?
- What happens when a source row has no previewable passage text?
- What happens when an answer has no sources at all?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The answer page for this increment MUST revert to the pre-`003-answer-graph-sources` answer-support structure before applying the newly requested presentation changes.
- **FR-002**: The system MUST NOT introduce a new standalone `Knowledge Graph` answer block as part of this increment.
- **FR-003**: The existing `流程拓扑` graph in the answer MUST continue to use ApeRAG's existing topology content source and generation path.
- **FR-004**: The `流程拓扑` graph MUST receive a rendering-only visual upgrade that aligns with the approved MiroFish graph style.
- **FR-005**: The graph rendering upgrade MUST preserve the user's ability to inspect the underlying topology data when the visual graph cannot be rendered.
- **FR-006**: The source-reference interaction MUST remain close to the original ApeRAG answer workflow rather than replacing the answer page with a new custom support layout.
- **FR-006A**: The source-reference entry mechanism MUST remain the original ApeRAG-style source entry and drawer behavior rather than moving the source list into a new inline answer block.
- **FR-007**: The source area MUST present one row per supporting source passage.
- **FR-008**: Each source row MUST identify the originating document.
- **FR-009**: Each source row MUST identify the supporting location using the best available locator, such as page, title, paragraph, or a clearly stated approximate location.
- **FR-010**: Users MUST be able to expand and collapse individual source rows within the source panel.
- **FR-011**: Expanding a source row MUST reveal the supporting passage inside the current answer context.
- **FR-012**: If exact paragraph precision is unavailable, the system MUST explicitly indicate that the location is approximate.
- **FR-013**: This increment MUST preserve Chinese-first behavior.
- **FR-014**: This increment MUST avoid unrelated visual or interaction changes outside the existing answer topology and source presentation surfaces.

### Key Entities *(include if feature involves data)*

- **Answer Topology Block**: The existing ApeRAG `流程拓扑` area rendered from the answer's current topology content.
- **Source Panel**: The existing answer-adjacent source entry area that lets users inspect supporting references.
- **Source Row**: One collapsible evidence row corresponding to one supporting passage from one document.
- **Source Locator**: The visible location marker that tells the user which page, title, paragraph, or approximate document section supports the answer.

## Assumptions

- The current system already produces answer text, topology content, and references for supported answers.
- The user-approved change is limited to presentation and interaction within the existing answer structure, not graph generation or retrieval redesign.
- The best available source locator may vary by document and parser output; when exact paragraph metadata is unavailable, the system should present the closest trustworthy locator instead of inventing precision.
- MiroFish is a visual reference for graph rendering quality in this increment, not a requirement to replace ApeRAG's existing topology content source.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of answers that already contain topology content continue to display that topology without introducing a new extra answer graph module.
- **SC-002**: Users can open the source panel and identify a supporting source row for an answer within one interaction from the answer area.
- **SC-003**: 100% of displayed source rows include document identity and a visible location marker.
- **SC-004**: Users can expand an individual source row and inspect its supporting passage without leaving the current answer context.
- **SC-005**: When exact paragraph precision is unavailable, the product communicates that limitation explicitly instead of implying a false exact citation.
- **SC-006**: Changes in this increment are confined to the existing answer topology and source presentation surfaces, with no unrelated chat-page layout changes required for users to complete the primary verification flow.
