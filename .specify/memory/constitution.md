<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- Template Principle 1 -> I. Business-Requirements-First, Incremental by Default
- Template Principle 2 -> II. Reference-First Reuse Over Net-New Code
- Template Principle 3 -> III. Unified Answer, Evidence, Graph Product Contract
- Template Principle 4 -> IV. UI Changes Require Explicit Authorization
- Template Principle 5 -> V. Server Reality Overrides Assumptions
Added sections:
- Implementation Boundaries
- Development Workflow & Quality Gates
Removed sections:
- None
Templates requiring updates:
- updated .specify/templates/plan-template.md
- updated .specify/templates/spec-template.md
- updated .specify/templates/tasks-template.md
- pending .specify/templates/commands/*.md (directory absent in this repository)
Follow-up TODOs:
- None
-->
# fuseAgent Constitution

## Core Principles

### I. Business-Requirements-First, Incremental by Default
Every `/speckit.specify` feature MUST map to the currently requested business
increment and the relevant sections of `BUSINESS-REQUIREMENTS.md`. Plans, tasks,
and implementation MUST stay inside that slice; unrelated requirements MUST be
called out as out of scope instead of being bundled into the same feature.
`/speckit.plan`, `/speckit.tasks`, and implementation MAY be automated after a
feature spec exists, but only for that approved increment, not for the full
product backlog.

This keeps scope reviewable and prevents one-shot overbuilding that hides
unfinished or unapproved work.

### II. Reference-First Reuse Over Net-New Code
Before introducing new architecture, modules, or UI, contributors MUST evaluate
whether the requirement can be satisfied by reusing or adapting code and
patterns from `E:\codes\fuseAgent_v2\LightRAG`,
`E:\codes\fuseAgent_v2\llm-graph-builder`, or
`E:\codes\fuseAgent_v2\MiroFish`. Major plans MUST name the candidate source or
sources for reuse and identify what will be copied, wrapped, or adapted.
Net-new code is allowed only when reuse is not viable for the current
increment, and that reason MUST be recorded in the plan or task notes.

This keeps delivery fast, reduces unnecessary reinvention, and grounds
implementation in proven code paths.

### III. Unified Answer, Evidence, Graph Product Contract
fuseAgent MUST ship as a single knowledge-base question answering product for
internal users, not as an engine comparison surface. Every user-facing Q&A
increment MUST preserve the contract defined in `BUSINESS-REQUIREMENTS.md`:
answer text, traceable evidence, and related graph are one coherent result.
When evidence is insufficient, the system MUST explicitly say "current evidence
insufficient" or the approved Chinese equivalent used by the product, and MUST
NOT fabricate support. Unless the user explicitly expands scope, v1 MUST remain
focused on single-knowledge-base Q&A, document management, evidence
traceability, and graph viewing for PDF, Word, Markdown, and TXT documents.

This preserves the core product promise and prevents the user experience from
drifting into a research console.

### IV. UI Changes Require Explicit Authorization
If the user has not provided specific UI requirements, contributors MUST NOT
invent new UI flows, visual concepts, or speculative interaction patterns.
Approved UI work MUST align with the business requirements and named references:
overall product UI follows ApeRAG and the provided prototypes; graph-related UI
follows MiroFish. Specs and plans MUST record whether a feature has `No UI
change`, `UI parity/adaptation`, or `New approved UI work`, and any UI tasks
outside that declaration are non-compliant.

This prevents unnecessary design churn and keeps the implementation faithful to
the product owner's intent.

### V. Server Reality Overrides Assumptions
Operational plans, scripts, and deployment steps MUST follow the user-provided
server reference file as the source of truth unless the user explicitly
overrides it. New server work MUST stay under
`/home/common/jyzhu/ucml`, prefer currently idle GPUs, and include local
port-forwarding to an available local port when remote services need access.
Features MUST be designed for the actual server and resource envelope rather
than assumed infrastructure.

This keeps delivery grounded in the environment that will actually run the
system.

## Implementation Boundaries

- `BUSINESS-REQUIREMENTS.md` is the governing product scope for fuseAgent.
- The default technical direction is retrieval and Q&A centered on LightRAG,
  extraction and graph construction centered on MiroFish, and selective
  reference to `llm-graph-builder` for graph, ingestion, and product patterns.
- The final product MUST hide underlying engine switching from end users unless
  the user explicitly asks for an internal evaluation surface.
- v1 defaults to internal-admin usage, single knowledge base workflows, and the
  document formats already listed in `BUSINESS-REQUIREMENTS.md`.
- Multi-tenant features, complex role systems, image-first understanding, and
  speculative platformization are out of scope until explicitly requested.

## Development Workflow & Quality Gates

- Every feature spec MUST include:
  business requirement traceability, the approved increment, explicit out of
  scope items, reference reuse candidates, and a UI scope declaration.
- Every implementation plan MUST pass a constitution check that answers:
  what increment is being built, what existing code will be reused, what UI
  scope is allowed, what server constraints apply, and what verification proves
  the change.
- Every task list MUST be ordered so the current increment can stop cleanly
  after a user story or checkpoint; unrelated backlog expansion is forbidden.
- Each implementation increment MUST include the smallest repeatable
  verification needed to prove the changed behavior. Changes touching answer,
  evidence, graph linkage, or deployment MUST include explicit validation for
  those behaviors.
- Merge or handoff review MUST confirm constitution compliance and record any
  approved exception in the relevant plan, task list, or review notes.

## Governance

This constitution supersedes local defaults for specs, plans, tasks, and
implementation decisions in this repository. Amendments require explicit user
approval and synchronization of dependent templates before they are considered
active. Versioning follows semantic rules for governance changes: MAJOR for
backward-incompatible principle changes or removals, MINOR for new principles
or materially expanded guidance, and PATCH for clarifications that do not alter
working expectations. Compliance review is mandatory for every generated or
manually edited spec, plan, tasks file, and implementation review.

**Version**: 1.0.0 | **Ratified**: 2026-03-21 | **Last Amended**: 2026-03-21
