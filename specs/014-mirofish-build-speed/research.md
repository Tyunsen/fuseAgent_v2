# Research: MiroFish Build Speed Recovery

## Decision 1: Use the recurring acceptance script as the authoritative measurement harness

- **Decision**: Treat `scripts/run_triple_trace_acceptance.py` as the authoritative recurring acceptance harness and harden it instead of relying on one-off manual runs.
- **Rationale**: The constitution requires recurring remote acceptance, so the measurement path itself must be reproducible and automatable.
- **Alternatives considered**:
  - Keep using manual browser checks. Rejected because they do not scale to per-feature recurring acceptance.
  - Add a separate external benchmarking tool. Rejected because the repo already contains the required APIs and remote tunnel helpers.

## Decision 2: Normalize unsupported acceptance files before upload rather than omitting them

- **Decision**: Preserve the content of unsupported `.json` and `.csv` acceptance files by converting them to markdown payloads during the acceptance import step.
- **Rationale**: The recurring acceptance dataset must be fully represented, but the current upload API rejects those source extensions directly.
- **Alternatives considered**:
  - Exclude unsupported files from acceptance. Rejected because the constitution now requires every accepted document to participate.
  - Broaden core product file-type support in this increment. Rejected because the speed-recovery increment can reach a useful acceptance path without widening the global parser surface first.

## Decision 3: Reduce graph build latency by lowering chunk count, not just by raising concurrency

- **Decision**: Optimize graph build throughput primarily through adaptive graph chunk sizing and related chunk-count controls.
- **Rationale**: The current acceptance workload is small enough in total bytes that the main cost is the number of extraction jobs, not raw file transfer volume.
- **Alternatives considered**:
  - Only increase extraction concurrency. Rejected because LLM throughput and persistence overhead still scale with chunk count.
  - Reduce ontology breadth. Rejected because that risks failing the graph density thresholds.

## Decision 4: Keep collection-level graph status as the authoritative truth

- **Decision**: Continue treating collection-level graph readiness as authoritative and avoid reintroducing document-level graph status as the acceptance truth for MiroFish collections.
- **Rationale**: MiroFish graph construction is collection-level by design, and earlier confusion came from exposing document-level `SKIPPED` states as if they represented graph failure.
- **Alternatives considered**:
  - Force a document-level graph-ready state for MiroFish. Rejected because it would distort the current graph model instead of clarifying it.

## Decision 5: Preserve the accepted graph workbench UI baseline

- **Decision**: Any graph/workbench UI adjustments in this increment must preserve the baseline represented by `ui-satisfied-graph-workbench`.
- **Rationale**: The user explicitly identified that branch as the accepted UI version, so performance work must not accidentally re-open UI churn.
- **Alternatives considered**:
  - Redesign the graph workbench while improving performance. Rejected because it broadens scope and risks breaking an already accepted UI.
