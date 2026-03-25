# Contract: Simplified Create Flow

## User-facing contract

- The `add` collection flow only exposes:
  - `title`
  - `description`
- The page keeps ApeRAG's create-page shell, breadcrumbs, and action placement.
- Successful create redirects to
  `/workspace/collections/{collectionId}/documents/upload`.

## Backend request contract

- Accepted minimal payload:
  - `title`
  - `description`
  - optional `type`
  - optional `config`
- If `config` is omitted or incomplete, the backend resolves hidden defaults and
  persists a valid MiroFish-mode `CollectionConfig`.

## Persistence contract

- The created collection stores:
  - hidden vector/fulltext defaults
  - resolved embedding/completion model defaults
  - MiroFish workflow metadata
  - initial graph status `waiting_for_documents`

## Compatibility rule

- Existing callers that still send the old full payload remain accepted.
- The simplified frontend path becomes the default create experience for this
  increment.
