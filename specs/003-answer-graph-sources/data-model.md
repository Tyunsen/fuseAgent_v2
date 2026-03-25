# Data Model: Answer Graph And Source Cards

## Answer Reference Row

- **Purpose**: One source row displayed inside the answer's inline source card.
- **Carrier**: Existing `Reference` object with enriched `metadata`.
- **Fields**:
  - `text`: cited paragraph or passage content
  - `score`: retrieval score for display only
  - `metadata.source_row_id`: stable UI row key
  - `metadata.collection_id`: source collection ID
  - `metadata.document_id`: source document ID
  - `metadata.document_name`: display name for the source document
  - `metadata.page_idx`: optional 0-based page index
  - `metadata.recall_type`: vector/fulltext/graph/summary/vision
  - `metadata.chunk_ids`: list of graph/source chunk IDs linked to this row
  - `metadata.paragraph_precise`: whether the row is paragraph-precise
  - `metadata.preview_title`: optional compact display title
- **Validation**:
  - `source_row_id` required for any displayed row
  - `document_name` should be present when known
  - `chunk_ids` may be empty, but then graph linking degrades explicitly

## Source Preview State

- **Purpose**: UI state for showing the original passage inline without leaving
  the answer context.
- **Fields**:
  - `expanded_source_row_ids`
  - `active_source_row_ids`
  - `scroll_target_source_row_id`
- **Rules**:
  - A row can be expanded without becoming the active linked row
  - Active highlighting may target one or more rows

## Answer Graph Query

- **Purpose**: Request contract used by the frontend to fetch one compact graph
  for one answer.
- **Fields**:
  - `source_row_ids`: optional list of visible row IDs
  - `chunk_ids`: deduplicated list of cited chunk/source IDs
  - `document_ids`: optional list of source documents
  - `max_nodes`: optional safety cap for answer-scoped rendering
- **Validation**:
  - `chunk_ids` is the primary query field
  - Empty `chunk_ids` produces a no-graph response, not an error

## Answer Graph Payload

- **Purpose**: Compact graph block shown inside one answer card.
- **Fields**:
  - `nodes`: graph nodes relevant to the cited answer support
  - `edges`: graph relationships relevant to the cited answer support
  - `linked_row_ids`: all row IDs represented in the graph
  - `is_empty`: whether graph support could not be derived
  - `empty_reason`: optional explicit no-graph reason
- **Rules**:
  - Payload must stay answer-scoped and not become a collection-wide graph dump
  - Graph elements must expose their linkage keys in properties/metadata

## Graph Element Link Metadata

- **Purpose**: Provides the bridge between graph clicks and source-row
  highlights.
- **Node Fields**:
  - `properties.chunk_ids`: list of supporting chunk/source IDs for the node
  - `properties.linked_row_ids`: resolved answer row IDs associated with the node
- **Edge Fields**:
  - `properties.chunk_ids`: list of supporting chunk/source IDs for the edge
  - `properties.linked_row_ids`: resolved answer row IDs associated with the edge
- **Rules**:
  - One graph element may map to many rows
  - One row may map to many graph elements
  - The frontend must treat these sets as many-to-many, not one-to-one

## Answer Support Block

- **Purpose**: The composite UI unit under the answer text.
- **Parts**:
  - `SourceCard`
  - `AnswerGraphBlock`
  - shared interaction state
- **Rules**:
  - Answer text renders independently
  - Source card and graph block may degrade independently
  - Bidirectional linking state is shared within one answer result only
