# Contract: Graph Start Scheduling

## Scope

This contract documents the expected behavior between document confirmation and
MiroFish collection graph-task submission for the current increment.

## Producer

- `aperag/service/document_service.py`

## Consumer

- `config.celery_tasks.mirofish_collection_graph_task`
- `aperag/service/mirofish_graph_service.py`

## Behavioral Contract

### 1. Successful confirmation for a MiroFish collection

- The service prepares a collection graph revision.
- If a revision is returned, the service submits
  `mirofish_collection_graph_task(collection_id, revision)`.
- Default behavior is immediate submission without a Celery `countdown`.

### 2. Explicit positive delay override

- If the runtime configuration explicitly supplies a positive MiroFish graph
  queue delay, the service may submit the same task with that `countdown`.
- This override does not change revision semantics or stale-revision handling.

### 3. Submission failure

- If the graph revision was prepared but the task submission call fails, the
  service invokes the existing graph failure finalization for that revision.
- The collection must not remain in a silently pending graph state caused only
  by submission failure.

### 4. Later execution safety

- Immediate submission does not bypass freshness checks.
- When the task executes, `mirofish_graph_service.py` remains responsible for
  skipping stale or already-synchronized revisions and preserving the active
  graph when appropriate.

## Observable Validation

- Immediate default start is observable through task submission behavior and
  worker logs.
- Positive-delay override is observable through the presence of a Celery
  countdown.
- Stale-revision safety is observable through existing skip results and graph
  lifecycle behavior.
