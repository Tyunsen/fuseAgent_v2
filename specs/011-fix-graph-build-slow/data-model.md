# Data Model: MiroFish Graph Start Latency Recovery

## Overview

This increment does not add a new persistent database entity. It clarifies the
runtime state and configuration objects that determine when a MiroFish graph
task is submitted after document confirmation.

## Entities

### 1. Graph Start Delay Policy

- **Purpose**: Defines whether the collection graph task should be submitted
  immediately or after an explicitly configured delay.
- **Fields**:
  - `delay_seconds`: Non-negative operator-controlled delay value
  - `is_immediate`: Derived flag indicating whether graph submission happens
    without Celery countdown
  - `source`: Default application behavior or explicit runtime override
- **Validation Rules**:
  - Delay values less than or equal to zero are treated as immediate start
  - Positive values are treated as explicit operator override, not default
    product behavior

### 2. Collection Graph Revision Request

- **Purpose**: Represents the latest requested graph state for a collection
  after documents are confirmed.
- **Fields**:
  - `collection_id`
  - `target_revision`
  - `has_active_graph`
  - `graph_status`
- **Validation Rules**:
  - Each successful confirmation that requires graph work advances the revision
  - The request remains subject to stale-revision checks before heavy work

### 3. Graph Task Submission Outcome

- **Purpose**: Captures whether the confirmation flow successfully submitted the
  graph task or failed before background execution began.
- **Fields**:
  - `submitted`: Whether the Celery task submission succeeded
  - `effective_delay_seconds`: The delay actually applied to task submission
  - `failure_reason`: Present only when submission fails
  - `revision`: The prepared target revision associated with the attempt
- **Validation Rules**:
  - Submission failure must route into the existing graph failure lifecycle
  - Immediate submission does not imply immediate graph completion

## State Transitions

### Confirmation to Graph Submission

1. Documents are confirmed successfully.
2. The collection graph revision is prepared.
3. The graph start delay policy is evaluated.
4. The graph task is submitted immediately when delay is not positive, or with
   an explicit countdown when a positive override exists.
5. If submission fails, the graph lifecycle records the failure for that
   revision.

### Submission to Execution Safety

1. Submitted graph tasks enter normal Celery execution.
2. `mirofish_graph_service.py` checks whether the revision is current, stale, or
   already synchronized.
3. Outdated work exits safely without replacing the active graph.
