# Feature Specification: MiroFish-Style Knowledge Base Creation

**Feature Branch**: `002-mirofish-kb-create`  
**Created**: 2026-03-21  
**Status**: Draft  
**Input**: User description: "Change the knowledge base creation process to
work like MiroFish, where users only provide the knowledge base name and its
intent/description to start building the graph, while keeping the page UI in
the ApeRAG style."

## Scope Alignment *(mandatory)*

- **Business Requirement Source**: `BUSINESS-REQUIREMENTS.md` sections 1, 5.1,
  6.1, 7.1, 8.1, 8.4, 10.1, and 12
- **Current Increment**: Replace the current complex new-knowledge-base setup
  with a simplified creation flow that asks only for the knowledge base name
  and the knowledge base intent/description, then starts the initial knowledge
  base setup/build process without requiring users to configure the advanced
  options exposed by the reused ApeRAG flow.
- **Out of Scope**: Redesigning the knowledge base homepage, changing document
  upload behavior, changing Q&A behavior beyond the existing ready/not-ready
  rules, adding new graph visualization pages, exposing advanced tuning after
  creation, changing model/provider administration, and any UI exploration that
  is not explicitly requested here.
- **Reference Reuse Candidates**: MiroFish simplified graph-initiation flow for
  the minimal input pattern and graph-processing behavior, existing
  fuseAgent/ApeRAG creation page shell and visual hierarchy for layout/style
  reuse, existing knowledge base list/detail flows for post-create navigation.
- **UI Scope**: UI parity-adaptation

## Clarifications

### Session 2026-03-21

- Q: After users submit the minimal name-and-intent form, should the system
  start graph building immediately, wait until document upload, or require a
  separate manual start step? -> A: Submit name and intent first to create the
  knowledge base shell; start the initial graph build when documents are first
  uploaded; treat later document uploads as graph updates, following the
  approved MiroFish graph-processing behavior.
- Q: After successful minimal creation, where should the user land, and should
  the old ApeRAG index options remain visible? -> A: Send the user directly to
  the created knowledge base's document management/upload page, and do not show
  the ApeRAG vector-index, full-text-index, or graph-index setup options in
  this increment because graph processing follows the approved MiroFish
  behavior.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create a Knowledge Base with Minimal Inputs (Priority: P1)

As an internal user, I want to create a knowledge base by entering only its
name and its intended purpose, so I can start building the knowledge base
without understanding or filling in a large set of technical settings.

**Why this priority**: Knowledge base creation is a core product entry point.
If the creation flow still feels heavy or technical, the product remains harder
to use than the approved MiroFish-style reference behavior.

**Independent Test**: Open the new knowledge base page, provide only the name
and intent/description, submit the form, and verify that the system accepts the
creation without requiring additional advanced configuration.

**Acceptance Scenarios**:

1. **Given** an authenticated internal user opens the new knowledge base page,
   **When** the page is displayed, **Then** the required information to create a
   knowledge base is limited to the knowledge base name and the knowledge base
   intent/description.
2. **Given** the user provides a valid name and intent/description, **When**
   the user confirms creation, **Then** the system creates the knowledge base
   without asking the user to complete the previously exposed advanced setup
   fields.
3. **Given** the user has not filled one or both required fields, **When** the
   user attempts to create the knowledge base, **Then** the system clearly
   explains what required information is missing.

---

### User Story 2 - Keep the Approved ApeRAG Visual Pattern (Priority: P2)

As an internal user, I want the simplified creation flow to still look and feel
like the approved ApeRAG management interface, so the product stays visually
consistent while the workflow becomes simpler.

**Why this priority**: The user explicitly approved reuse of ApeRAG's UI style
and explicitly rejected unrequested UI invention. The visual shell must remain
consistent while only the creation logic and required inputs are simplified.

**Independent Test**: Compare the new knowledge base page before and after this
increment and verify that the page still uses the existing ApeRAG-style layout
and hierarchy while removing the unneeded advanced configuration sections and
index-setting areas.

**Acceptance Scenarios**:

1. **Given** the user opens the simplified creation page, **When** the page
   structure is shown, **Then** the layout remains visually aligned with the
   approved ApeRAG management style rather than switching to a different product
   style.
2. **Given** the simplified creation page is displayed, **When** the user scans
   the form, **Then** the page does not add new visual modules, decorative
   sections, or workflow steps that were not explicitly requested.
3. **Given** the simplified creation page replaces the previous complex form,
   **When** the user views the form body, **Then** the removed advanced setup
   areas, including the ApeRAG vector-index, full-text-index, and graph-index
   setup options, are not shown as required or primary inputs for this
   increment.

---

### User Story 3 - Start Initial Setup Automatically After Creation (Priority: P3)

As an internal user, I want the system to begin the initial knowledge base
setup/build process through the normal document-upload flow after I provide the
minimal information, so I do not have to manually configure internal
graph-building or indexing choices before the knowledge base can start
processing.

**Why this priority**: The point of the MiroFish-style flow is not only a
smaller form. It also shifts hidden technical choices away from the user and
lets the system proceed from business intent directly into setup.

**Independent Test**: Create a knowledge base with only the required inputs,
verify that the resulting knowledge base shell appears with a clear next-step
state, then upload documents and verify that the first upload starts the
initial graph build while later uploads are treated as updates.

**Acceptance Scenarios**:

1. **Given** the user successfully creates a knowledge base with the minimal
   input form, **When** the creation completes, **Then** the resulting knowledge
   base shell is created and the user is taken directly to that knowledge
   base's document management/upload page with a clear next-step or
   not-ready-yet state.
2. **Given** the user uploads documents to a newly created knowledge base shell
   for the first time, **When** the upload is accepted, **Then** the system
   starts the initial graph build without requiring a separate manual start
   action.
3. **Given** the user uploads additional documents after the initial graph
   build has already started or completed, **When** the upload is accepted,
   **Then** the system treats that upload as a graph update rather than as a
   brand-new knowledge base setup flow.
4. **Given** the graph-processing work has not finished yet, **When** the user
   returns to the created knowledge base, **Then** the product clearly
   communicates that the knowledge base is still processing rather than implying
   it is fully ready.

### Edge Cases

- What happens when the user enters a name but leaves the intent/description
  empty?
- What happens when the user enters an intent/description but leaves the name
  empty?
- What happens when the user submits a name that is already in use or too close
  to an existing knowledge base to distinguish clearly?
- What happens when the user submits very short or very long intent text?
- What happens when creation succeeds but the initial setup/build process has
  not finished by the time the user returns to the knowledge base list?
- How does the product explain that a knowledge base shell has been created but
  the first graph build has not started yet because no documents have been
  uploaded?
- How does the product explain a failure if the system cannot start the initial
  graph build after the first document upload?
- What happens when the user uploads more documents while a previous graph
  processing or update cycle is still running?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The new knowledge base flow in this increment MUST collect only
  two required business inputs from the user: the knowledge base name and the
  knowledge base intent/description.
- **FR-002**: The system MUST NOT require users to configure the advanced
  creation settings that were previously exposed in the reused ApeRAG-based
  creation flow for this increment.
- **FR-003**: The simplified creation page MUST NOT display the ApeRAG
  vector-index, full-text-index, or graph-index setup options in this
  increment.
- **FR-004**: The simplified creation flow MUST remain inside an ApeRAG-style
  management page shell and MUST preserve the approved overall visual language
  for this product area.
- **FR-005**: The simplified creation flow MUST NOT introduce additional
  workflow steps, helper panels, or exploratory UI sections that were not
  explicitly requested.
- **FR-006**: Users MUST be able to start knowledge base creation from the
  existing management flow and complete it using only the required name and
  intent/description inputs.
- **FR-007**: The system MUST clearly indicate when either required field is
  missing or invalid.
- **FR-008**: After successful submission, the system MUST create the knowledge
  base and take the user directly to the created knowledge base's document
  management/upload page.
- **FR-009**: After successful submission of the minimal form, the system MUST
  create a knowledge base shell even before documents are uploaded.
- **FR-010**: The first accepted document upload to a newly created knowledge
  base shell MUST start the initial graph build without requiring a separate
  manual start action.
- **FR-011**: Later document uploads to an existing knowledge base MUST be
  handled as graph updates rather than as a brand-new knowledge base setup
  flow.
- **FR-012**: Any hidden setup choices needed to begin graph processing MUST be
  handled internally by the system rather than being exposed as required user
  decisions in this increment.
- **FR-013**: The created knowledge base MUST expose a clear readiness,
  processing, not-ready-yet, or waiting-for-documents state after creation so
  users understand whether downstream work can begin.
- **FR-014**: The simplified creation flow MUST remain aligned with the
  authenticated internal-user operating model already defined for this product
  and MUST NOT become a public pre-login flow.
- **FR-015**: The simplified creation flow MUST preserve Chinese-first product
  behavior already established for the current workspace.
- **FR-016**: The document-triggered initial graph build and later graph-update
  behavior in this increment MUST follow the approved MiroFish reference
  behavior rather than reintroducing the previously exposed ApeRAG-style manual
  setup choices.

### Key Entities *(include if feature involves data)*

- **Knowledge Base Draft**: The temporary user-provided creation input that
  contains only the knowledge base name and intent/description before the
  knowledge base is created.
- **Knowledge Base Intent**: The user-written statement of what the knowledge
  base is for, which guides the system's initial setup/build process without
  requiring exposed advanced configuration.
- **Knowledge Base**: The created business object that becomes visible in the
  management flow after successful submission.
- **Knowledge Base Shell**: The newly created knowledge base record that exists
  after the user submits only the name and intent/description but before the
  first document-triggered graph build begins.
- **Initial Setup State**: The post-creation lifecycle state that communicates
  whether the knowledge base is waiting for documents, building its first graph,
  updating an existing graph, or ready for downstream work.

## Assumptions

- This increment changes only the creation flow and its visible input scope; it
  does not redefine the broader homepage, document management, or Q&A product
  areas beyond clarifying how the first document upload triggers initial graph
  building and how later uploads trigger graph updates.
- The existing ApeRAG-style page shell remains the approved visual reference
  for this screen, while MiroFish is used as the approved interaction reference
  for the simplified "minimal inputs, create shell, then build through document
  upload" behavior.
- Internal defaults are acceptable for setup choices that were previously shown
  as advanced form settings, because the user explicitly asked to remove that
  complexity from the creation flow.
- The approved MiroFish reference behavior covers both the first document-
  triggered graph build and later document-triggered graph updates.
- Post-creation downstream rules such as "not ready yet" behavior continue to
  follow the existing product expectations already defined in prior increments.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete the new knowledge base creation form in no
  more than 1 minute when they already know the intended name and purpose.
- **SC-002**: 100% of successful knowledge base creations in this increment can
  be completed with no more than 2 required fields.
- **SC-003**: Users can identify the required information for the creation flow
  without needing to interpret technical configuration terminology.
- **SC-004**: After successful submission, users can find the newly created
  knowledge base's document management/upload page without navigating through
  unrelated pages.
- **SC-005**: After successful submission, users receive a visible
  waiting-for-documents, processing, updating, or readiness signal for the
  created knowledge base rather than an ambiguous completion state.
