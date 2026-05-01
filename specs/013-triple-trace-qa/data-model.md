# Data Model: Knowledge Base Triple Trace QA

## Knowledge Base Purpose Signal

- **Purpose**: The collection-level business purpose used to bias ontology generation and extraction emphasis.
- **Source of truth**: Existing collection metadata, primarily `description` with `title` fallback.
- **Key attributes**:
  - `collectionId`
  - `title`
  - `purposeText`
  - `additionalContext`
- **Rule**: This is the only business-intent input for extraction in this increment.

## Ontology Profile

- **Purpose**: The effective ontology definition used to extract entities and relations from document chunks.
- **Key attributes**:
  - `baseEntityTypes`: Fixed broad entity type catalog always present.
  - `baseRelationTypes`: Fixed broad relation type catalog always present.
  - `supplementalEntityTypes`: Lightweight knowledge-base-purpose-driven additions produced by the LLM.
  - `supplementalRelationTypes`: Lightweight knowledge-base-purpose-driven additions produced by the LLM.
  - `entityTypeCap`
  - `relationTypeCap`
  - `sourceTextBudget`
- **Validation rules**:
  - Base types must always survive validation.
  - Supplemental types must remain broad and deduplicated against the base catalog.
  - Final caps must exceed the current 10/10 clamp but remain bounded for latency.

## Traceable Attribute Set

- **Purpose**: The optional time and place attributes that can be attached directly to extracted entities and extracted relationships.
- **Possible attributes**:
  - `time`
  - `time_start`
  - `time_end`
  - `time_label`
  - `place`
  - `place_normalized`
  - `place_aliases`
- **Validation rules**:
  - Attributes are stored only when source evidence supports them.
  - Missing time/place stays missing; there is no inferred filler value.
  - Entity and relation attributes follow the same evidence rule.

## Extracted Entity

- **Purpose**: A graph node retained from source text and reused by default and trace modes.
- **Key attributes**:
  - `id`
  - `name`
  - `entityType`
  - `description`
  - `attributes`
  - `sourceChunkIds`
- **Relationships**:
  - May link to many extracted relationships.
  - May carry traceable time/place attributes when explicitly supported.

## Extracted Relationship

- **Purpose**: A graph edge connecting two extracted entities.
- **Key attributes**:
  - `id`
  - `sourceEntityId`
  - `targetEntityId`
  - `relationType`
  - `description`
  - `keywords`
  - `attributes`
  - `sourceChunkIds`
- **Validation rules**:
  - Relation time/place attributes are optional and evidence-backed.
  - Relation type names must normalize to a single canonical label in the final ontology profile.

## Trace Mode

- **Purpose**: The answer-organization mode selected by the user.
- **Allowed values**:
  - `default`
  - `time`
  - `space`
  - `entity`
- **Rule**: `default` preserves the current answer behavior; the other three modes reuse the same retrieval channels and reorganize the answer and graph around one selected dimension.

## Trace Retrieval Context

- **Purpose**: The normalized evidence package prepared after the default mixed retrieval path completes.
- **Key attributes**:
  - `traceMode`
  - `question`
  - `normalizedFocus`
  - `vectorDocs`
  - `fulltextDocs`
  - `graphDocs`
  - `referenceRows`
  - `graphEvidence`
- **Mode-specific behavior**:
  - `time`: normalize user phrasing into a target date or date range and rank evidence by temporal fit.
  - `space`: normalize the requested place and rank evidence by place match or place-neighbor support.
  - `entity`: normalize the focal entity and rank evidence by entity match and connection strength.

## Major Conclusion Binding

- **Purpose**: One displayed answer-level finding linked to concrete source rows.
- **Key attributes**:
  - `id`
  - `title`
  - `statement`
  - `sourceRowIds`
  - `locatorQuality`
  - `timeLabel`
  - `placeLabel`
  - `focusEntity`
- **Validation rules**:
  - Every displayed conclusion must reference at least one existing source row.
  - `locatorQuality` must distinguish exact from approximate support.
  - Optional time/place/entity labels must reflect the strongest available evidence for the selected mode.

## Trace Graph Payload

- **Purpose**: The mode-specific graph representation shown alongside the answer.
- **Key attributes**:
  - `traceMode`
  - `layout`
  - `nodes`
  - `edges`
  - `groups`
  - `legend`
  - `emptyReason`
- **Layout expectations**:
  - `time`: ordered or grouped by date/period.
  - `space`: centered or grouped by place.
  - `entity`: centered on the focal entity and its strongest neighbors.

## Trace Support Response

- **Purpose**: The post-answer payload that feeds conclusion-level citations and the selected trace graph.
- **Key attributes**:
  - `traceMode`
  - `conclusions`
  - `graph`
  - `evidenceSummary`
  - `fallbackUsed`
- **Rule**: When structured evidence is weak, the response still returns usable conclusions and explicitly signals fallback behavior instead of failing.
