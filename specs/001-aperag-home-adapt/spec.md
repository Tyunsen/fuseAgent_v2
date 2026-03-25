# Feature Specification: ApeRAG-Style Knowledge Base Homepage

**Feature Branch**: `001-aperag-home-adapt`  
**Created**: 2026-03-21  
**Status**: Draft  
**Input**: User description: "Adapt ApeRAG as the base homepage, remove the introduction page, default the interface to Chinese, and remove the top-right utility icons."

## Scope Alignment *(mandatory)*

- **Business Requirement Source**: `BUSINESS-REQUIREMENTS.md` sections 1, 4.3, 5.1, 6.1, 7.1, 8.1, 8.4, 10.1, and 12
- **Current Increment**: Deliver the first fuseAgent homepage increment as a knowledge base management entry that stays visually close to the approved ApeRAG reference, opens directly into work instead of an introduction page, defaults to Chinese, removes the right-top utility icons that are not needed for business work, keeps the full approved knowledge base creation form scope from the reference for this first pass, and provides real usable document management and Q&A destinations from each listed knowledge base.
- **Out of Scope**: Marketplace views, documentation center, GitHub links, language switching UI, theme tools, graph customization beyond the reused reference behavior, evidence-focused fuseAgent customizations beyond the reused reference behavior, and any new UI ideas not explicitly requested here.
- **Reference Reuse Candidates**: ApeRAG knowledge base homepage, ApeRAG knowledge base creation flow, ApeRAG document management pages, ApeRAG Q&A pages, ApeRAG workspace header hierarchy, and ApeRAG Chinese-first labels where reuse is viable for this increment.
- **UI Scope**: UI parity-adaptation

## Clarifications

### Session 2026-03-21

- Q: For this increment, should the create-knowledge-base page keep the full reference form scope or only a minimal name-and-description version? -> A: Keep the full approved reference form scope for now and simplify later in follow-up increments if needed.
- Q: For this increment, should the homepage remain behind login or be visible before login? -> A: Keep the login gate and route authenticated users directly to the knowledge base homepage after sign-in.
- Q: When users enter document management and Q&A from the homepage, should those destinations be real usable pages or only placeholder shells? -> A: They must be real usable pages in this increment, aligned closely with the ApeRAG reference except for the explicitly removed items.
- Q: What should remain in the top-right area after removing the non-business utility icons? -> A: Keep only the user menu in the top-right area; remove language, GitHub, documentation/help, theme, and similar utility entries.
- Q: How should the Q&A entry behave when the knowledge base is still being built or incrementally updated? -> A: Block Q&A before the first build completes, then allow Q&A during later incremental updates with a clear stale-results warning.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Direct Knowledge Base Homepage (Priority: P1)

As an internal user, I want to enter the system after sign-in and immediately
see a Chinese knowledge base management homepage, so I can start managing
knowledge bases without going through a marketing or introduction page.

**Why this priority**: The business requirement is to let users "directly start
working". If the first screen is wrong, the product already misses its main
goal.

**Independent Test**: Sign in as an internal user and verify that the first
visible page after authentication is the Chinese knowledge base homepage with
list, search, and create entry, and that no introduction page appears.

**Acceptance Scenarios**:

1. **Given** an internal user signs in to fuseAgent, **When** the initial
   authenticated page loads, **Then** the user lands directly on the knowledge
   base homepage instead of an introduction page.
2. **Given** the homepage loads for a first authenticated visit, **When**
   labels and controls are shown, **Then** the interface is presented in
   Chinese by default without requiring a language switch.
3. **Given** the authenticated user has existing knowledge bases, **When** the
   homepage is displayed, **Then** the page shows a clear list of those
   knowledge bases and a visible search entry.

---

### User Story 2 - Create a Knowledge Base from the Homepage (Priority: P2)

As an internal user, I want to start a new knowledge base from the homepage, so
I can begin building a workspace without searching through extra pages.

**Why this priority**: Knowledge base creation is the first business action in
the product's core flow and must be easy to start from the main entry page.

**Independent Test**: From the homepage, start a new knowledge base, complete
the full approved creation form scope used in this increment, submit it, and
verify the new knowledge base is visible in the management list.

**Acceptance Scenarios**:

1. **Given** the user is on the homepage, **When** the user selects the create
   knowledge base entry, **Then** the system opens a Chinese knowledge base
   creation flow without showing the removed utility icons and with the full
   approved form scope preserved for this increment.
2. **Given** the user provides valid information across the full approved
   creation form scope, **When** the user confirms creation, **Then** the new
   knowledge base appears in the homepage management list.
3. **Given** the user starts but does not finish creation, **When** the user
   cancels or leaves the flow, **Then** no unintended knowledge base is created
   and the user can return to the homepage safely.

---

### User Story 3 - Enter Work Areas from Each Knowledge Base (Priority: P3)

As an internal user, I want each knowledge base on the homepage to provide
direct entry into document management and Q&A, so I can move straight from
management into work.

**Why this priority**: The homepage is meant to be an operational entry, not
just a list. Direct work-area access is required by the business requirements.

**Independent Test**: From the homepage, select a listed knowledge base and use
its document management entry and its Q&A entry, verifying the chosen knowledge
base context is preserved and that both destinations are actually usable.

**Acceptance Scenarios**:

1. **Given** the user sees a listed knowledge base on the homepage, **When**
   the user selects its document management entry, **Then** the system opens
   the document management area for that specific knowledge base and the user
   can perform its core document operations there.
2. **Given** the user sees a listed knowledge base on the homepage, **When**
   the user selects its Q&A entry, **Then** the system opens the Q&A area for
   that specific knowledge base and the user can perform the core Q&A behavior
   there.
3. **Given** a knowledge base is not yet ready for a work area, **When** the
   user views its homepage entry, **Then** the page shows a clear status or
   limitation instead of implying the work area is fully available.
4. **Given** a knowledge base has not finished its first build, **When** the
   user tries to enter or use Q&A, **Then** the system blocks the Q&A flow and
   clearly explains that question answering is unavailable until initial
   processing completes.
5. **Given** a knowledge base is undergoing later incremental updates,
   **When** the user enters or uses Q&A, **Then** the system allows question
   answering but clearly warns that the current results may lag behind the
   latest document changes.

### Edge Cases

- What happens when there are no knowledge bases yet and the user opens the
  homepage for the first time?
- How does the homepage behave when a search returns no matching knowledge
  bases?
- What happens when a knowledge base exists but is missing optional descriptive
  information?
- How does the homepage communicate that a knowledge base is not yet ready for
  Q&A or other downstream work areas?
- What happens when a user enters document management or Q&A from the homepage
  but the selected knowledge base has no content yet?
- What happens when the first knowledge base build is still processing and the
  user attempts to start Q&A anyway?
- What happens when an incremental update is processing and the user asks a
  question before the latest content is fully indexed?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST route users directly to the knowledge base
  homepage as the initial working entry for this increment after sign-in.
- **FR-002**: The system MUST NOT show the ApeRAG-style introduction or
  marketing homepage in this increment.
- **FR-003**: The homepage in this increment MUST remain an authenticated
  internal-user page and MUST NOT become a public pre-login landing page.
- **FR-004**: The system MUST default the homepage and knowledge base creation
  flow to Chinese for first-visit users.
- **FR-005**: The homepage MUST remain visually close to the approved ApeRAG
  management style and MUST avoid adding new visual sections that were not
  explicitly requested.
- **FR-006**: The homepage MUST display a list of knowledge bases available to
  the current internal user.
- **FR-007**: Users MUST be able to search the knowledge base list by visible
  identifying information such as name and description.
- **FR-008**: The homepage MUST provide a clear create-knowledge-base entry.
- **FR-009**: The knowledge base creation flow MUST preserve the full approved
  knowledge base creation form scope used by the ApeRAG reference for this
  first increment.
- **FR-010**: After a knowledge base is created successfully, the system MUST
  make the new knowledge base visible from the homepage without requiring the
  user to hunt through unrelated pages.
- **FR-011**: Each listed knowledge base MUST show enough summary information
  for the user to distinguish it from other knowledge bases.
- **FR-012**: Each listed knowledge base MUST provide a direct entry to
  document management.
- **FR-013**: Each listed knowledge base MUST provide a direct entry to Q&A.
- **FR-014**: The document management destination opened from the homepage MUST
  be actually usable in this increment and MUST preserve the selected knowledge
  base context.
- **FR-015**: The Q&A destination opened from the homepage MUST be actually
  usable in this increment and MUST preserve the selected knowledge base
  context.
- **FR-016**: If the selected knowledge base has not completed its first build,
  the system MUST block Q&A and clearly state that question answering is not yet
  available.
- **FR-017**: If the selected knowledge base is under later incremental
  updates, the system MUST allow Q&A to continue but MUST clearly warn that the
  returned result may be stale.
- **FR-018**: The homepage MUST show a clear empty state when no knowledge
  bases exist or when search produces no matches, and that empty state MUST
  preserve a visible next action.
- **FR-019**: The top-right utility icons from the ApeRAG reference homepage,
  including language, GitHub, documentation/help, and similar non-business
  shortcuts, MUST NOT appear in this increment's homepage shell.
- **FR-020**: The homepage MUST preserve only business-essential header content
  and MUST NOT expose promotional or community navigation as primary entry
  points.
- **FR-021**: After removing the non-business utility icons, the homepage
  header MUST retain only the authenticated user menu as the top-right control
  area.
- **FR-022**: If a listed knowledge base is not yet ready for downstream work,
  the homepage MUST communicate that state clearly rather than pretending the
  destination is fully available.

### Key Entities *(include if feature involves data)*

- **Knowledge Base**: The main managed business object, with identifying
  information, a current state, and direct destinations for document management
  and Q&A.
- **Knowledge Base Homepage Entry**: The user-facing management representation
  of a knowledge base on the homepage, including search visibility, summary
  details, and work-area entry actions.
- **Knowledge Base Draft**: The set of basic user-provided details collected
  during the create-knowledge-base flow before it becomes a managed knowledge
  base.
- **Knowledge Base Processing State**: The readiness state that determines
  whether Q&A is blocked for the initial build or allowed with warnings during
  incremental updates.
- **Document Management Workspace**: The usable work area for managing the
  selected knowledge base's documents after entering from the homepage.
- **Q&A Workspace**: The usable work area for asking questions within the
  selected knowledge base after entering from the homepage.

## Assumptions

- v1 users operate with internal admin-level capability as defined in
  `BUSINESS-REQUIREMENTS.md`.
- This increment preserves the existing sign-in gate and only changes the first
  authenticated destination and homepage presentation.
- This increment includes real usable document management and Q&A destinations
  reached from the homepage, aligned closely with the ApeRAG reference except
  for the explicitly removed items.
- ApeRAG is the approved visual reference for page structure and interaction
  hierarchy, but fuseAgent content replaces ApeRAG's product introduction and
  external/community shortcuts.
- The first-pass create-knowledge-base flow keeps the full approved reference
  scope; simplification of fields is deferred to later increments.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After sign-in, users reach the knowledge base homepage without
  encountering an introduction page.
- **SC-002**: 100% of first authenticated homepage sessions show Chinese labels
  without requiring manual language switching.
- **SC-003**: Users can locate a target knowledge base from the homepage in no
  more than 3 interactions.
- **SC-004**: Users can start a new knowledge base from the homepage and submit
  its basic information in under 2 minutes.
- **SC-005**: Users can reach and begin using document management for a listed
  knowledge base in a single homepage selection.
- **SC-006**: Users can reach and begin using Q&A for a listed knowledge base
  in a single homepage selection.
- **SC-007**: For a knowledge base whose first build is incomplete, users are
  prevented from starting Q&A and see a clear blocking explanation.
- **SC-008**: For a knowledge base under incremental update, users can continue
  Q&A and see a clear warning that results may lag behind the latest changes.
