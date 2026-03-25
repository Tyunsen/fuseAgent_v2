# Implementation Plan: ApeRAG-Style Knowledge Base Homepage

**Branch**: `001-aperag-home-adapt` | **Date**: 2026-03-21 | **Spec**: `E:\codes\fuseAgent_v2\fuseAgent\specs\001-aperag-home-adapt\spec.md`  
**Input**: Feature specification from `E:\codes\fuseAgent_v2\fuseAgent\specs\001-aperag-home-adapt\spec.md`

## Summary

Implement the first fuseAgent increment by importing ApeRAG as the execution baseline, then applying only the approved adaptations: remove the marketing/intro entry page, default the product to Chinese, keep only the user menu in the right-top control area, and expose direct knowledge-base list/search/create/document/Q&A entry flows. The Q&A entry for this increment reuses ApeRAG's collection search workspace because it is the closest existing operational query surface and keeps the "copy first, refine later" constraint intact.

## Technical Context

**Language/Version**: Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend  
**Primary Dependencies**: ApeRAG backend stack, Celery, SQLAlchemy/FastAPI-adjacent service layer, Next.js 15, next-intl, Tailwind CSS 4, Radix UI  
**Storage**: PostgreSQL, Redis, Qdrant, Elasticsearch, optional Neo4j, local object storage  
**Testing**: Frontend lint/build smoke checks, route-level manual verification, backend startup validation, deployment smoke on target Linux server  
**Target Platform**: Linux server deployment plus local Windows development workspace  
**Project Type**: Full-stack web application  
**Performance Goals**: Preserve ApeRAG baseline responsiveness for authenticated list/search/create/document/query flows and support the business requirement scale of hundreds of documents per knowledge base  
**Constraints**: Stay inside the approved increment, prefer direct reuse over net-new code, do not add unrequested UI, keep auth gate, deploy only under `/home/common/jyzhu/ucml`, prefer idle GPU for embedding work, keep runtime secrets out of committed docs and code  
**Scale/Scope**: Internal admin-style users, single deployed product shell, first increment focused on knowledge base homepage plus real document/Q&A destinations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Scope is limited to the approved increment and mapped to sections 1, 4.3, 5.1, 6.1, 7.1, 8.1, 8.4, 10.1, and 12 of `BUSINESS-REQUIREMENTS.md`.
- [x] Out-of-scope items remain explicit: marketing homepage, GitHub/docs/language/theme controls, marketplace-centric entry points, and speculative UI additions.
- [x] Reuse is primary: ApeRAG provides the concrete homepage/create/document/search stack; LightRAG remains part of inherited backend behavior; net-new code is limited to route/header/list adaptations and deployment glue.
- [x] UI impact matches the spec's `UI parity-adaptation` scope.
- [x] Server work follows the user-provided server note: target host, target base directory, idle GPU preference, and local port forwarding.
- [x] Verification will prove the approved behaviors for direct homepage entry, Chinese default locale, create flow, document entry, and Q&A entry/status handling.

## Phase 0 Research

See `research.md` for the decisions that resolve implementation unknowns. The planning conclusions used by implementation are:

1. Copy the ApeRAG repository structure into `fuseAgent` instead of re-implementing features from scratch.
2. Reuse `web/src/app/workspace/collections/*` as the homepage/create/document baseline.
3. Treat `web/src/app/workspace/collections/[collectionId]/search/*` as the first-pass Q&A workspace because it is the existing per-collection query surface.
4. Remove the right-top GitHub/docs/theme/locale controls in `web/src/components/app-topbar.tsx` and keep only the authenticated user menu.
5. Replace the root landing page with an authenticated work-entry redirect instead of a marketing page.
6. Configure deployment from the inherited ApeRAG Docker/Python/Next stack, with server-specific env overrides added outside committed secrets.

## Phase 1 Design

### Data Model

See `data-model.md`. The increment centers on:

- Knowledge Base
- Knowledge Base Homepage Entry
- Knowledge Base Draft
- Knowledge Base Processing State
- Document Management Workspace
- Query Workspace

### Interface Contracts

See `contracts/navigation.md` and `contracts/deployment-env.md`.

### Quickstart

See `quickstart.md` for the local and server validation paths that implementation must satisfy.

## Project Structure

### Documentation (this feature)

```text
specs/001-aperag-home-adapt/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── deployment-env.md
│   └── navigation.md
└── tasks.md
```

### Source Code (repository root)

```text
.specify/
specs/
aperag/
config/
deploy/
envs/
resources/
tests/
web/
├── deploy/
├── package.json
└── src/
    ├── app/
    ├── components/
    ├── i18n/
    ├── lib/
    └── services/
Dockerfile
docker-compose.yml
docker-compose.deploy.remote.yml
pyproject.toml
uv.lock
```

**Structure Decision**: Use ApeRAG's existing full-stack repository layout unchanged where possible. This keeps backend/frontend/service wiring intact and minimizes integration risk for the first increment.

## Implementation Strategy

### Phase 1: Baseline Migration

- Copy ApeRAG repository contents into the current repo, excluding ApeRAG's `.git` directory.
- Preserve existing `.specify/`, `specs/`, and agent workflow files.
- Keep ApeRAG's backend, frontend, env, deploy, and docker assets as the starting point.

### Phase 2: Product Entry Adaptation

- Replace `/` marketing behavior with direct work-entry routing.
- Default locale to Chinese by environment and server-side locale fallback.
- Remove right-top utility controls from the top bar while keeping the user menu.
- Keep workspace auth gate and `/workspace/collections` as the main destination.

### Phase 3: Homepage and Work-Area Adaptation

- Reuse the ApeRAG collection list and full collection creation form.
- Add direct per-collection actions for document management and Q&A/search from the homepage list.
- Keep document management pages intact unless small label/routing adjustments are required.
- Use the collection search page as the Q&A destination for this increment.
- Surface processing-state restrictions so first-build collections cannot enter usable Q&A and incremental-update collections show a stale-results warning.

### Phase 4: Deployment Adaptation

- Prepare local env examples for Chinese-first fuseAgent defaults.
- Add or adjust server-side deployment commands/scripts under the allowed server directory.
- Configure the embedding worker to use an idle GPU on the target server when available.
- Configure the LLM provider endpoint in deployment env without committing the supplied secret values.

## Post-Design Constitution Check

- [x] No new feature areas were added beyond homepage/create/document/query entry.
- [x] Reuse remains the dominant strategy; all major UI and service flows come from ApeRAG.
- [x] Planned deployment work is limited to the user-provided server and inherited stack.
- [x] The design still avoids speculative UI changes.

## Complexity Tracking

No constitution violations require justification for this increment.
