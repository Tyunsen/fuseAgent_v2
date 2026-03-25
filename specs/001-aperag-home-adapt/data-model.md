# Data Model: ApeRAG-Style Knowledge Base Homepage

## Knowledge Base

- Source: Inherited ApeRAG collection entity
- Purpose: Primary managed business object shown on the homepage and used as the context for documents and query/Q&A work.
- Key fields:
  - `id`
  - `title`
  - `description`
  - `created`
  - `status`
  - `subscription_id`
  - `config`
  - `is_published`
- Relationships:
  - Has many documents
  - Has many search/query results
  - Has many question sets/evaluations
  - Owns a processing/readiness state used by homepage and Q&A entry gating

## Knowledge Base Homepage Entry

- Purpose: User-facing card/list item on `/workspace/collections`.
- Derived from:
  - Knowledge base identity fields
  - Status fields
  - Summary fields
  - Direct action URLs
- Required behavior:
  - Visible in search results by title and description
  - Exposes direct actions to:
    - `/workspace/collections/{collectionId}/documents`
    - `/workspace/collections/{collectionId}/search`
  - Shows empty-state guidance when there are no results

## Knowledge Base Draft

- Purpose: The data captured by the full ApeRAG collection creation form before and during submission.
- Source: Reused ApeRAG collection form state
- Required behavior:
  - Preserve the full reference form scope in this increment
  - On successful submission, materialize as a visible knowledge base entry in the homepage list
  - On cancellation/abandonment, do not create a persistent knowledge base

## Knowledge Base Processing State

- Purpose: Determines whether downstream work areas are ready and how Q&A entry is presented.
- Observed state signals:
  - Active/inactive/deleted collection status
  - Per-document processing/indexing status
  - Collection update activity inferred from inherited ApeRAG processing state
- Required transitions:
  - Initial build pending -> Q&A blocked with explanation
  - Active and current -> Q&A allowed normally
  - Incremental update in progress -> Q&A allowed with stale-results warning

## Document Management Workspace

- Route: `/workspace/collections/{collectionId}/documents`
- Purpose: Operational area for uploading, listing, viewing, deleting, replacing, and monitoring document processing for a knowledge base.
- Inputs:
  - `collectionId`
  - Current document list and processing statuses
- Outputs:
  - Document upload/update/delete actions
  - Status visibility for document readiness

## Query Workspace

- Route: `/workspace/collections/{collectionId}/search`
- Purpose: First-pass per-knowledge-base Q&A/search area reused from ApeRAG.
- Inputs:
  - `collectionId`
  - Query text
  - Enabled retrieval modes from collection config
- Outputs:
  - Search/query history
  - Query results and detail drawers
  - Blocking or warning status when knowledge-base processing state requires it
