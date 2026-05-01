# Research: MiroFish Graph Start Latency Recovery

## Decision 1: Treat the fixed post-confirm delay as the primary regression

- **Decision**: Fix the immediate regression at the graph-task submission layer
  instead of assuming the graph extraction engine itself became slower.
- **Rationale**: `aperag/service/document_service.py` currently defines
  `MIROFISH_GRAPH_QUEUE_DELAY_SECONDS = 10` and always submits the collection
  graph task with `countdown=10`, which guarantees the graph path starts later
  than vector/fulltext even before any graph workload begins.
- **Alternatives considered**:
  - Tune graph extraction concurrency first: rejected because it does not
    address the guaranteed 10-second idle wait before work starts.
  - Redesign Celery routing or queues: rejected as a larger change than needed
    for the current increment.

## Decision 2: Keep stale-revision protection as the safety mechanism

- **Decision**: Reuse the freshness checks already present in
  `aperag/service/mirofish_graph_service.py` to protect against rapid successive
  confirms after removing the fixed submission delay.
- **Rationale**: The service already skips stale or already-synchronized
  revisions at preflight and major checkpoints, which is the correct place to
  coalesce outdated work.
- **Alternatives considered**:
  - Preserve the 10-second delay as a debounce mechanism: rejected because it
    trades user-visible latency for safety that is already handled elsewhere.
  - Add a new external lock or queue coalescer: rejected because current
    revision semantics already encode the required freshness signal.

## Decision 3: Use a setting-backed delay policy with default immediate start

- **Decision**: Move the graph queue delay to settings with a default of `0`
  and omit Celery `countdown` when the effective delay is not positive.
- **Rationale**: This restores immediate behavior by default while still
  allowing an operator override if a future environment explicitly needs a
  small delay for troubleshooting or workload shaping.
- **Alternatives considered**:
  - Hardcode `countdown=0`: rejected because a setting-backed policy is more
    observable and easier to override without another code change.
  - Remove all delay logic entirely: rejected because leaving a documented
    override path is a low-cost operational safeguard.

## Decision 4: Validate with both unit tests and the provided `iw_docs` dataset

- **Decision**: Add targeted unit tests for scheduling behavior and use
  `E:\codes\fuseAgent_v2\iw_docs` as the smoke dataset for realistic validation.
- **Rationale**: The regression is about observed workflow timing, so unit
  coverage alone is insufficient; however, realistic smoke validation without
  unit regression tests would leave the scheduling rule easy to break again.
- **Alternatives considered**:
  - Unit tests only: rejected because they do not prove the intended operator
    validation path.
  - Full performance benchmark suite: rejected as too large for the current
    increment.
