# Tasks: ApeRAG-Style Knowledge Base Homepage

**Input**: Design documents from `E:\codes\fuseAgent_v2\fuseAgent\specs\001-aperag-home-adapt\`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`

**Tests**: This increment relies on smoke validation and targeted lint/build checks instead of net-new automated test suites. Verification tasks are included for every user story because behavior proof is required.

**Organization**: Tasks are grouped by user story so the homepage entry, create flow, and document/Q&A entry can each be validated independently.

## Constitution Requirements

- Tasks stay inside the approved increment.
- Reuse/adaptation tasks appear before net-new changes.
- UI work is limited to ApeRAG parity adaptation and removal of explicitly rejected controls.
- Deployment tasks stay on the user-provided server path and inherited ApeRAG stack.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Import the approved baseline and preserve the local speckit workflow files.

- [X] T001 Copy ApeRAG repository contents into `E:\codes\fuseAgent_v2\fuseAgent\` while excluding `E:\codes\fuseAgent_v2\ApeRAG\.git`
- [X] T002 Reconcile ignore and workspace baseline files in `E:\codes\fuseAgent_v2\fuseAgent\.gitignore`, `E:\codes\fuseAgent_v2\fuseAgent\.dockerignore`, and `E:\codes\fuseAgent_v2\fuseAgent\AGENTS.md`
- [X] T003 [P] Prepare inherited env defaults for local development in `E:\codes\fuseAgent_v2\fuseAgent\envs\env.template` and `E:\codes\fuseAgent_v2\fuseAgent\web\deploy\env.local.template`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared shell and deployment prerequisites required by all user stories.

- [X] T004 Configure Chinese-first locale fallback in `E:\codes\fuseAgent_v2\fuseAgent\web\src\services\cookies.ts`
- [X] T005 [P] Simplify the shared top bar to user-menu-only in `E:\codes\fuseAgent_v2\fuseAgent\web\src\components\app-topbar.tsx`
- [X] T006 [P] Remove non-business workspace entry points from the shared shell in `E:\codes\fuseAgent_v2\fuseAgent\web\src\app\workspace\menu-main.tsx`
- [X] T007 [P] Add remote deployment and port-forward helper scripts in `E:\codes\fuseAgent_v2\fuseAgent\scripts\deploy-fuseagent-remote.sh` and `E:\codes\fuseAgent_v2\fuseAgent\scripts\connect-fuseagent-remote.ps1`
- [X] T008 Prepare remote runtime env templates for fuseAgent deployment in `E:\codes\fuseAgent_v2\fuseAgent\envs\env.remote.template` and `E:\codes\fuseAgent_v2\fuseAgent\docker-compose.deploy.remote.yml`

**Checkpoint**: Baseline repo, locale defaults, shared shell, and deployment helpers are ready.

---

## Phase 3: User Story 1 - Direct Knowledge Base Homepage (Priority: P1) MVP

**Goal**: Users sign in and land directly on a Chinese knowledge base homepage instead of a marketing page.

**Independent Test**: Open the app, verify `/` no longer renders the intro page, verify unauthenticated access still routes through sign-in, then verify authenticated entry lands on `/workspace/collections` with Chinese UI and only the user menu in the top-right shell.

- [X] T009 [US1] Replace the marketing landing page with a direct work-entry redirect in `E:\codes\fuseAgent_v2\fuseAgent\web\src\app\page.tsx`
- [X] T010 [US1] Preserve authenticated workspace entry routing in `E:\codes\fuseAgent_v2\fuseAgent\web\src\app\workspace\page.tsx` and `E:\codes\fuseAgent_v2\fuseAgent\web\src\app\workspace\layout.tsx`
- [X] T011 [US1] Adapt the knowledge base homepage shell copy and layout in `E:\codes\fuseAgent_v2\fuseAgent\web\src\app\workspace\collections\page.tsx`
- [X] T012 [US1] Keep list/search/empty-state behavior aligned with the homepage spec in `E:\codes\fuseAgent_v2\fuseAgent\web\src\app\workspace\collections\collection-list.tsx`
- [ ] T013 [US1] Run frontend smoke verification for direct homepage entry from `E:\codes\fuseAgent_v2\fuseAgent\web`

**Checkpoint**: User Story 1 is complete when sign-in drops users into the Chinese knowledge base homepage with no intro page.

---

## Phase 4: User Story 2 - Create a Knowledge Base from the Homepage (Priority: P2)

**Goal**: Users can open and submit the full ApeRAG-style knowledge base creation form from the homepage.

**Independent Test**: From `/workspace/collections`, open the create flow, submit the full reused form, confirm redirect back to the list, and confirm cancellation does not create an unintended knowledge base.

- [X] T014 [US2] Reuse the inherited create page entry in `E:\codes\fuseAgent_v2\fuseAgent\web\src\app\workspace\collections\new\page.tsx`
- [X] T015 [US2] Preserve the full ApeRAG collection form scope in `E:\codes\fuseAgent_v2\fuseAgent\web\src\app\workspace\collections\collection-form.tsx`
- [X] T016 [US2] Ensure create success and cancel paths return correctly to the homepage list in `E:\codes\fuseAgent_v2\fuseAgent\web\src\app\workspace\collections\collection-form.tsx`
- [ ] T017 [US2] Run smoke verification for create and cancel behavior from `E:\codes\fuseAgent_v2\fuseAgent\web`

**Checkpoint**: User Story 2 is complete when the full create flow works from the homepage and returns users cleanly to the list.

---

## Phase 5: User Story 3 - Enter Work Areas from Each Knowledge Base (Priority: P3)

**Goal**: Each homepage knowledge base entry offers direct document management and Q&A entry using the inherited ApeRAG workspaces.

**Independent Test**: From the homepage, use the explicit document-management and Q&A actions on a collection, confirm the selected collection context is preserved, confirm the search page functions as Q&A, and confirm first-build/incremental-update messaging is visible when relevant.

- [X] T018 [US3] Add explicit document-management and Q&A actions to each homepage knowledge base entry in `E:\codes\fuseAgent_v2\fuseAgent\web\src\app\workspace\collections\collection-list.tsx`
- [X] T019 [US3] Keep the document management route aligned with the selected collection context in `E:\codes\fuseAgent_v2\fuseAgent\web\src\app\workspace\collections\[collectionId]\documents\page.tsx`
- [X] T020 [US3] Reuse the collection search page as the Q&A destination and surface collection readiness messaging in `E:\codes\fuseAgent_v2\fuseAgent\web\src\app\workspace\collections\[collectionId]\search\page.tsx`
- [X] T021 [US3] Block first-build Q&A and warn on incremental-update Q&A in `E:\codes\fuseAgent_v2\fuseAgent\web\src\app\workspace\collections\[collectionId]\search\search-test.tsx`
- [X] T022 [US3] Add matching document/Q&A navigation affordances inside the collection header in `E:\codes\fuseAgent_v2\fuseAgent\web\src\app\workspace\collections\[collectionId]\collection-header.tsx`
- [ ] T023 [US3] Run smoke verification for homepage-to-documents and homepage-to-Q&A flows from `E:\codes\fuseAgent_v2\fuseAgent\web`

**Checkpoint**: User Story 3 is complete when both work areas are directly reachable from the homepage and reflect collection readiness state correctly.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final fuseAgent adaptation, deployment configuration, and validation.

- [X] T024 [P] Replace obvious ApeRAG branding defaults used by this increment in `E:\codes\fuseAgent_v2\fuseAgent\web\deploy\env.local.template`, `E:\codes\fuseAgent_v2\fuseAgent\web\deploy\yaml\configmap.yaml`, and `E:\codes\fuseAgent_v2\fuseAgent\deploy\aperag\values.yaml`
- [X] T025 [P] Add fuseAgent-specific remote runtime defaults for model and embedding services in `E:\codes\fuseAgent_v2\fuseAgent\envs\env.remote.template`
- [ ] T026 Deploy the adapted stack to the user-provided server from `E:\codes\fuseAgent_v2\fuseAgent\scripts\deploy-fuseagent-remote.sh`
- [X] T027 Configure local remote-access forwarding in `E:\codes\fuseAgent_v2\fuseAgent\scripts\connect-fuseagent-remote.ps1`
- [ ] T028 Run final local and remote validation from `E:\codes\fuseAgent_v2\fuseAgent\web` and `E:\codes\fuseAgent_v2\fuseAgent\scripts`

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (Phase 1) starts immediately.
- Foundational (Phase 2) depends on Setup completion and blocks all user stories.
- User Story 1 starts after Foundational and establishes the MVP.
- User Story 2 depends on the reused repo baseline and homepage shell from User Story 1.
- User Story 3 depends on the homepage list from User Story 1 and reused collection workspaces from the copied ApeRAG baseline.
- Polish depends on all selected user stories being complete.

### User Story Dependencies

- User Story 1 is the MVP and has no dependency on later stories.
- User Story 2 depends on User Story 1 because the homepage is the create entry point.
- User Story 3 depends on User Story 1 because the homepage list is the work-area launch surface.

### Parallel Opportunities

- T003, T005, T006, T007, T024, and T025 can run in parallel because they touch different files.
- After the shared shell is in place, User Story 2 and User Story 3 can be finished sequentially with minimal file overlap.

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete User Story 1.
3. Verify the direct knowledge base homepage flow.

### Incremental Delivery

1. Add the full create flow from User Story 2.
2. Add direct document/Q&A entry from User Story 3.
3. Finish deployment and remote validation.

## Notes

- The implementation is intentionally reuse-heavy; if ApeRAG already provides a working flow, adapt it before writing new code.
- The first-pass Q&A destination is the inherited collection search workspace, not the evaluation question-set pages.
- Remote secrets are injected at deploy time and must not be committed.
