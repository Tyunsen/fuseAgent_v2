# Feature Specification: Knowledge Base Triple Trace QA

**Feature Branch**: `013-triple-trace-qa`  
**Created**: 2026-04-03  
**Status**: Draft  
**Input**: User description: "Refine the knowledge-base triple-trace plan by preserving the current default QA mode, adding time/space/entity trace modes, strengthening extraction so entities and relationships keep time and place attributes when supported, relying only on knowledge-base purpose rather than a global system intent, binding major conclusions to concrete document fragments, and providing a graph view for each trace mode."

## Clarifications

### Session 2026-04-03

- Q: 三脉络应建立在什么数据组织基础上？ → A: 直接基于现有实体、关系及其时间/地点属性做三脉络，不新增中间层。
- Q: 时间/地点属性的承载范围怎么定？ → A: 实体和关系都允许带时间/地点属性，但只在源文档明确支持时才保留。
- Q: 三个脉络模式里的检索结果，应该怎么和默认模式的检索融合？ → A: 复用默认检索通道，再做定向筛选、排序、组织。
- Q: 三脉络的图展示应该如何设计？ → A: 做三种明显不同的图形组织，而不是只在同一个基础图上切换强调方式。
- Q: ontology 类型的来源怎么定？ → A: 保留固定通用基础类型，再按知识库意图补充覆盖更宽的特有类型；补充生成应保持轻量，不要臃肿。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask in Default or Trace Mode (Priority: P1)

As an analyst using a knowledge base, I want to choose between the current default answer mode and three trace modes for time, space, and entity views, so I can either get a general answer or a trace-organized answer without changing my question-writing habits.

**Why this priority**: The primary value of this increment is not only better extraction but a controllable answer experience. If users cannot intentionally switch between the current default mode and the three trace modes, the trace feature has no practical entry point.

**Independent Test**: Open the chat experience for a knowledge base, ask the same question in default mode and in each of the three trace modes, and verify that the default mode remains available while each trace mode reorganizes the answer around its selected dimension.

**Acceptance Scenarios**:

1. **Given** a user opens knowledge-base Q&A, **When** no trace mode is selected, **Then** the system uses the current default answer mode rather than forcing a trace-specific answer path.
2. **Given** a user selects the time trace mode, **When** the user asks a question such as "What happened in March?", **Then** the answer is organized around the relevant time range rather than only as a general summary.
3. **Given** a user selects the space trace mode, **When** the user asks a question about a place such as "What happened in Abu Dhabi?", **Then** the answer is organized around that place and its nearby supporting context.
4. **Given** a user selects the space trace mode, **When** the user asks about a place, **Then** the system locks onto one focal location and presents a time-ordered gantt-style view for events tied to that location.
5. **Given** a user selects the entity trace mode, **When** the user asks a question focused on a person, organization, or object, **Then** the answer is organized around that entity and its relevant connected facts.
6. **Given** a trace mode is selected but structured evidence for that dimension is incomplete, **When** the answer is generated, **Then** the system still returns a usable answer and clearly reflects the strongest available traceable evidence instead of failing silently.

---

### User Story 2 - Preserve Time and Place in Extraction (Priority: P1)

As a knowledge-base owner, I want the extracted entities and relationships to preserve time and place information whenever the source text provides it, so later answers can be organized into time, space, and entity traces without inventing missing facts.

**Why this priority**: The three trace modes depend on the extraction result carrying the right traceable attributes. If time and place are not retained during extraction, the later trace answers and graph views cannot be reliable.

**Independent Test**: Ingest documents that mention dates, periods, locations, and location aliases, then verify that the extracted knowledge retains those attributes when they are present and does not fabricate them when they are absent.

**Acceptance Scenarios**:

1. **Given** a source fragment explicitly states when something happened, **When** knowledge is extracted from that fragment, **Then** the resulting knowledge retains the available time information in a reusable form.
2. **Given** a source fragment explicitly states where something happened, **When** knowledge is extracted from that fragment, **Then** the resulting knowledge retains the available place information in a reusable form.
3. **Given** a source fragment supports an entity or relationship but does not state time or place, **When** knowledge is extracted, **Then** the system does not invent time or place values.
4. **Given** a knowledge base has a defined business purpose, **When** extraction guidance is determined, **Then** the system uses that knowledge-base purpose to guide entity and relationship emphasis rather than relying on a separate hard-coded global domain intent.
5. **Given** knowledge is extracted from a document, **When** later answers cite that knowledge, **Then** the system can still trace it back to the supporting document fragment.

---

### User Story 3 - Verify Conclusions with Trace Graphs and Citations (Priority: P2)

As an analyst reading an answer, I want each important conclusion to show which document fragment supports it and to see a graph view aligned with the selected trace mode, so I can quickly verify the answer and understand its structure.

**Why this priority**: Trace answers are only trustworthy if users can see where key conclusions came from and how the answer is structured. Citations and graph presentation are the proof layer of this increment.

**Independent Test**: Ask questions in each trace mode, then verify that the answer presents mode-appropriate graph content and that each major conclusion can be tied to one or more concrete supporting fragments from the source documents.

**Acceptance Scenarios**:

1. **Given** an answer contains multiple major findings, **When** the answer is displayed, **Then** each finding shows at least one visible supporting citation to a concrete document fragment.
2. **Given** a user opens a displayed citation, **When** the evidence view appears, **Then** the user can identify the source document and the supporting fragment within the current answer context.
3. **Given** the selected trace mode is time, **When** the graph is shown, **Then** the graph emphasizes temporal ordering or temporal grouping of the supporting knowledge.
4. **Given** the selected trace mode is space, **When** the graph is shown, **Then** the graph locks onto one focal location and presents the related events in a time-ordered gantt-style view for that location.
5. **Given** the selected trace mode is entity, **When** the graph is shown, **Then** the graph emphasizes the focal entity and its most relevant linked knowledge.
6. **Given** exact fragment precision is unavailable for a cited source, **When** the citation is displayed, **Then** the system clearly labels the locator as approximate instead of implying false precision.

### Edge Cases

- What happens when a user does not choose any trace mode and expects the current answer behavior to remain unchanged?
- What happens when a user asks for a month, date range, or relative time phrase but the supporting documents only provide partial time information?
- What happens when a place appears under multiple names, spellings, or aliases across documents?
- What happens when an entity name is ambiguous and matches multiple entities in the knowledge base?
- What happens when a document supports a conclusion but does not provide trustworthy time or place information?
- What happens when a trace mode is selected but the strongest evidence comes from the default retrieval path rather than from already structured graph data?
- What happens when a citation can identify the document and fragment text but cannot provide an exact paragraph or page locator?
- What happens when the answer contains evidence that fits more than one trace dimension at the same time?
- What happens when the knowledge-base-specific type guidance is too narrow and causes valid entities or relationships to be missed?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST preserve the current default knowledge-base answer mode and make it the fallback behavior when no trace mode is selected.
- **FR-002**: The system MUST provide three additional answer modes for time trace, space trace, and entity trace.
- **FR-003**: Each trace mode MUST reorganize answer content around its selected dimension while still answering the user's original question.
- **FR-004**: The system MUST interpret natural-language requests for time, place, and entity focus within the selected trace mode without requiring users to write formal filters.
- **FR-005**: All three trace modes MUST continue to use the same knowledge-base scope and the same existing evidence channels that already support the default answer mode rather than replacing them with a trace-only path.
- **FR-005A**: The three trace modes MUST reuse the default knowledge-base retrieval path as their base and then apply mode-specific filtering, ranking, and organization rather than introducing an entirely separate retrieval system for this increment.
- **FR-006**: Knowledge extraction MUST retain time information on entities and relationships when the source content explicitly provides it and when that time information is relevant to the extracted fact.
- **FR-007**: Knowledge extraction MUST retain place information on entities and relationships when the source content explicitly provides it and when that place information is relevant to the extracted fact.
- **FR-007A**: Both extracted entities and extracted relationships MAY carry time and place attributes for this increment, but only when those attributes are explicitly supported by source evidence.
- **FR-008**: The system MUST NOT invent time or place attributes when the source material does not support them.
- **FR-009**: Extraction guidance for entity and relationship emphasis MUST be derived from the knowledge base's configured purpose and MUST NOT rely on a separate hard-coded system-wide intent.
- **FR-009A**: Entity and relationship extraction for this increment MUST start from a fixed set of broad, reusable base types rather than relying only on free-form type generation.
- **FR-009B**: The knowledge base purpose MAY supplement those base types with additional knowledge-base-specific types, and those supplemental types MUST remain broad enough to improve coverage rather than narrowing extraction so much that valid entities or relationships are omitted.
- **FR-009C**: Determining any knowledge-base-specific supplemental types MUST remain a lightweight part of extraction guidance and MUST NOT become a heavyweight standalone step that materially delays extraction startup.
- **FR-010**: The extracted knowledge used by this increment MUST remain traceable to concrete supporting document fragments.
- **FR-010A**: The three trace modes MUST be built directly on the existing extracted entities, extracted relationships, and their retained time/place attributes, and MUST NOT require a new intermediate fact-unit layer or a separate event-centered data model for this increment.
- **FR-011**: Answers in all modes MUST present visible support for their major conclusions rather than only showing a general source list for the whole answer.
- **FR-012**: Every displayed major conclusion MUST be linked to at least one supporting document fragment.
- **FR-013**: Each displayed citation MUST identify the source document and present the best available trustworthy fragment locator.
- **FR-014**: If exact fragment precision is unavailable, the system MUST explicitly indicate that the citation locator is approximate.
- **FR-015**: The time trace mode MUST present answer findings in a time-oriented structure that helps users understand order, period, or change over time.
- **FR-016**: The space trace mode MUST present answer findings in a location-oriented structure that helps users understand what happened at, around, or across places.
- **FR-016A**: The space trace mode MUST lock onto one focal location for each answer result and MUST organize that location's related events in time order.
- **FR-016B**: The space trace mode MUST render a gantt-style time view for the focal location, and the gantt entries MUST only contain events tied to that location.
- **FR-017**: The entity trace mode MUST present answer findings in an entity-oriented structure that helps users understand a focal entity and its related knowledge.
- **FR-018**: The system MUST provide a graph view for each trace mode, and each graph view MUST visually emphasize the selected trace dimension.
- **FR-018A**: The graph presentation for time trace, space trace, and entity trace MUST be meaningfully distinct from one another in how they organize and present supporting knowledge, rather than differing only by minor highlighting within one unchanged graph layout.
- **FR-019**: The graph view for each trace mode MUST remain consistent with the answer findings and their displayed citations.
- **FR-020**: If a trace mode has insufficient structured evidence to fully organize the answer, the system MUST still return a usable answer and clearly surface the strongest available evidence.
- **FR-021**: This increment MUST remain confined to knowledge-base Q&A and MUST NOT introduce a separate system-wide intent layer outside the knowledge base.
- **FR-022**: This increment MUST preserve Chinese-first presentation behavior.

### Key Entities *(include if feature involves data)*

- **Knowledge Base Purpose**: The configured business purpose of a knowledge base that guides which domain concepts deserve emphasis during extraction.
- **Base Type Set**: The stable broad entity and relationship types that provide a reusable starting point for extraction across knowledge bases.
- **Extracted Entity**: A knowledge item representing a person, organization, place, object, activity, or other domain concept retained from source text.
- **Extracted Relationship**: A traceable connection between extracted entities, optionally carrying relevant time and place information when supported by source text.
- **Supplemental Type Set**: The additional knowledge-base-purpose-driven entity and relationship types that broaden extraction coverage for a specific knowledge base without replacing the base type set.
- **Traceable Attribute Set**: The retained time and place attributes attached directly to extracted entities and extracted relationships when source evidence supports them.
- **Trace Mode Answer**: A knowledge-base answer rendered in default, time, space, or entity mode, with organization rules that match the selected view.
- **Major Conclusion**: A key answer finding that the user can read as a discrete claim or takeaway and that must be supported by evidence.
- **Supporting Fragment**: The concrete document snippet used to support an extracted fact or a displayed answer conclusion.
- **Trace Graph View**: The mode-specific graph representation whose structure differs by time, space, or entity mode so users can understand the supporting knowledge through the selected trace lens.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can ask the same question in default mode and in each of the three trace modes without changing the wording of the question.
- **SC-002**: 100% of answers generated in a selected trace mode visibly reflect that mode in both answer organization and graph presentation.
- **SC-003**: 100% of displayed major conclusions include at least one visible supporting citation to a concrete document fragment or an explicitly marked approximate locator.
- **SC-004**: Users can identify the supporting document fragment for a displayed major conclusion in under 10 seconds after the answer appears.
- **SC-005**: When source material explicitly provides time or place information for a displayed fact, that information is available for trace-mode organization rather than being lost during extraction.
- **SC-006**: When time or place information is absent from source material, the system communicates trace limits through weaker organization or approximate evidence rather than inventing unsupported facts.
- **SC-007**: Users can understand whether an answer is organized by time, by space, by entity, or by the default mode within one glance at the answer result.
- **SC-008**: Using the acceptance document set under `E:\codes\fuseAgent_v2\iw_docs`, the system completes vector, fulltext, and graph indexing within 4 minutes of starting the full import.
- **SC-009**: On the collection graph page for the acceptance knowledge base, the rendered graph contains more than 80 nodes and more than 100 relationships.
- **SC-010**: In default mode, 100% of validated answers present text, visible citations, a topology/process graph, and a source list together.
- **SC-011**: In time trace mode, 100% of validated answers add a gantt-style time view with day-level precision when the source evidence supports day-level dates.
- **SC-012**: In space trace mode, 100% of validated answers lock onto a single focal location and add a time-ordered gantt-style view containing only events tied to that location.
- **SC-013**: In entity trace mode, 100% of validated answers add a knowledge subgraph whose displayed entities and edges are limited to the entities and edges involved in the current answer.

## Assumptions

- The current default knowledge-base Q&A behavior is already valuable and should remain available as the baseline mode rather than being replaced.
- The project-level constitution defines `E:\codes\fuseAgent_v2\iw_docs` as the mandatory recurring acceptance dataset for indexing, graph, and QA validation.
- The product already has knowledge extraction, document-backed evidence, and at least one answer-related graph presentation path that this increment can build upon.
- The existing default retrieval path already provides useful evidence and should be reused as the base of the three trace modes instead of being bypassed.
- Knowledge bases can carry a defined purpose or usage orientation that is sufficient to guide extraction emphasis without adding a separate global intent layer.
- A mixed type strategy is preferred: stable broad base types first, then lightweight knowledge-base-specific supplementation aimed at wider coverage rather than tight restriction.
- This increment should extend the current entity-and-relationship foundation rather than introducing a new intermediate knowledge layer.
- The three trace modes should feel visually distinct in graph presentation, not merely like one reused graph with superficial emphasis changes.
- Time and place remain optional evidence-backed attributes rather than mandatory fields for every extracted entity or relationship.
- Source documents vary in quality, so some citations may need to rely on the best trustworthy fragment locator rather than an exact paragraph or page number.
- When source material does not explicitly support time or place, the correct behavior is to preserve uncertainty instead of fabricating completeness.
