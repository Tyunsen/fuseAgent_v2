# Contract: Recurring Acceptance Report

## Scope

This contract defines the minimum structured output that recurring acceptance
automation must emit for the MiroFish build speed recovery feature.

## Contract

1. Every acceptance run MUST emit a structured report.
2. The report MUST include:
   - local forwarded web and API URLs
   - acceptance collection identifier
   - collection-level graph status and active graph identifier when available
   - document count observed during the run
   - total elapsed seconds measured against the indexing budget
   - collection graph node and edge counts
   - one result entry per validated QA mode
   - overall pass/fail plus explicit failure reasons
3. When the acceptance run fails before all phases complete, the report MUST still
   be emitted and MUST preserve any partial evidence collected so far.
4. The recurring acceptance report MUST be understandable without inspecting raw logs.

## Latest Passing Evidence

- Run date: 2026-04-04 (Asia/Shanghai) / 2026-04-03 18:54 UTC
- Command: `python scripts/run_triple_trace_acceptance.py`
- Remote stack: `/home/common/jyzhu/ucml/fuseAgent-current`
- Local forwarded web: `http://127.0.0.1:46130/`
- Local forwarded API docs: `http://127.0.0.1:46180/docs`
- Acceptance collection: `colaf374753c4084435`
- Graph status: `ready`
- Active graph id: `graph_bc4e7ba4f6a44c87d3d00ce6`
- Elapsed indexing time: `172.83s`
- Graph density: `248` nodes / `214` edges
- Mode validation:
  - `default`: passed
  - `time`: passed
  - `space`: passed
  - `entity`: passed
- Overall result: passed
