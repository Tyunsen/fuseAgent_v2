# Data Model: MiroFish Build Speed Recovery

## Acceptance Run

- **Purpose**: One complete recurring acceptance execution from remote stack start through final validation.
- **Key attributes**:
  - `runId`
  - `startedAt`
  - `finishedAt`
  - `durationSeconds`
  - `passed`
  - `failureReasons`

## Acceptance Collection

- **Purpose**: The fresh knowledge base created for one recurring acceptance run.
- **Key attributes**:
  - `collectionId`
  - `title`
  - `graphStatus`
  - `activeGraphId`
  - `documentCount`

## Acceptance Import Source

- **Purpose**: One source file from `iw_docs`, including any normalized upload form used during acceptance.
- **Key attributes**:
  - `sourcePath`
  - `sourceType`
  - `uploadFilename`
  - `normalizedForUpload`
  - `includedInAcceptance`

## Graph Build Profile

- **Purpose**: The chunking and extraction profile used for one MiroFish build.
- **Key attributes**:
  - `baseChunkSize`
  - `adaptiveChunkSize`
  - `chunkOverlap`
  - `chunkCount`
  - `extractionConcurrency`

## Graph-Ready Payload

- **Purpose**: The graph data and metadata returned once the collection graph is ready.
- **Key attributes**:
  - `graphId`
  - `nodeCount`
  - `edgeCount`
  - `renderable`
  - `schemaCompatible`

## Mode Contract Result

- **Purpose**: Validation result for one QA mode during recurring acceptance.
- **Key attributes**:
  - `mode`
  - `query`
  - `answerPresent`
  - `citationsPresent`
  - `requiredVisualizationPresent`
  - `notes`

## Acceptance Report

- **Purpose**: The structured output emitted by the recurring acceptance script.
- **Key attributes**:
  - `user`
  - `localUrls`
  - `collection`
  - `documents`
  - `graphCounts`
  - `modeResults`
  - `passed`
  - `failures`
