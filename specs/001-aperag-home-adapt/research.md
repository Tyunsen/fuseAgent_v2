# Research: ApeRAG-Style Knowledge Base Homepage

## Decision 1: Use ApeRAG as the implementation baseline

- Decision: Copy the ApeRAG repository structure and code into `fuseAgent`, then adapt the minimum set of files required by the spec.
- Rationale: The user explicitly asked for "basically copy it" and the current repo is almost empty. Reuse eliminates unnecessary reimplementation risk and keeps behavior close to the approved reference.
- Alternatives considered:
  - Rebuild only the homepage shell from scratch. Rejected because it violates the reuse-first instruction and creates avoidable divergence.
  - Copy only the frontend. Rejected because document/search/create flows depend on the inherited backend and deployment stack.

## Decision 2: Use `/workspace/collections` as the authenticated home

- Decision: Replace the root landing behavior with a redirect into `/workspace/collections`.
- Rationale: ApeRAG already redirects `/workspace` to `/workspace/collections`, and the spec requires the first authenticated destination to be the knowledge base homepage without a marketing page.
- Alternatives considered:
  - Keep ApeRAG's `/` marketing page and change button copy. Rejected because the spec forbids showing the introduction page.
  - Build a new custom dashboard. Rejected because it adds UI work outside scope.

## Decision 3: Default locale to Chinese at both env and server fallback levels

- Decision: Change the default locale from `en-US` to `zh-CN` in the frontend env template and in the server-side locale fallback logic.
- Rationale: Environment defaults alone are not sufficient if the env var is missing; the server fallback must also match the approved default behavior.
- Alternatives considered:
  - Only update env templates. Rejected because missing env values would fall back to English.
  - Keep the locale switcher visible. Rejected because the user explicitly removed it from the top-right controls.

## Decision 4: Keep only the user menu in the top-right control area

- Decision: Remove GitHub, docs/help, locale, and theme controls from the shared topbar and leave only the authenticated user menu.
- Rationale: This is explicitly required in the spec and is a small, localized change in `web/src/components/app-topbar.tsx`.
- Alternatives considered:
  - Hide those controls only on the homepage. Rejected because the spec describes the adapted shell, not only a single screen.
  - Keep theme switching. Rejected because the user grouped it with the utility icons to remove.

## Decision 5: Treat ApeRAG collection search as the first-pass Q&A workspace

- Decision: Map the homepage "问答" entry to `web/src/app/workspace/collections/[collectionId]/search`.
- Rationale: ApeRAG's `questions` area is evaluation/question-set management, while `search` is the existing per-collection query/test surface that users can actually use to ask queries and inspect results immediately. This best satisfies "usable Q&A destination" without inventing a new UI.
- Alternatives considered:
  - Use `questions` as the Q&A entry. Rejected because it is not the primary interactive query experience.
  - Build a new chat page for this increment. Rejected because it is outside the approved scope and unnecessary given the reuse directive.

## Decision 6: Add direct homepage actions instead of repurposing the whole collection card

- Decision: Keep the collection cards but add explicit "文档管理" and "问答" actions on each knowledge base entry.
- Rationale: The spec requires direct entry to both work areas from the homepage. ApeRAG cards currently deep-link only to documents, so explicit actions are the smallest change that satisfies the requirement clearly.
- Alternatives considered:
  - Keep card click for documents and ask users to enter Q&A from the collection header after navigation. Rejected because it fails the direct-entry requirement.
  - Split the list into separate document/Q&A tables. Rejected because it is unnecessary UI churn.

## Decision 7: Represent build-state Q&A restrictions in the reused query workspace

- Decision: Reuse collection status/config information to block or warn around the search/Q&A entry.
- Rationale: The spec requires first-build blocking and incremental-update warning. The homepage and query entry must communicate these states even if ApeRAG's baseline wording is adapted.
- Alternatives considered:
  - Ignore the state for now because ApeRAG does not exactly match the requirement. Rejected because the clarified spec kept this behavior.
  - Hide the Q&A entry entirely for non-ready collections. Rejected because the spec calls for clear status/limitation communication, not silent disappearance.

## Decision 8: Deploy using the inherited ApeRAG stack on the provided server

- Decision: Reuse ApeRAG's Python/Docker/Next deployment assets and adapt env/runtime configuration for fuseAgent on the user-provided server.
- Rationale: The repo already contains Docker, compose, and env templates. Reusing them is faster and safer than inventing new deployment infrastructure.
- Alternatives considered:
  - Create a brand-new deployment layout. Rejected because it adds avoidable operational work.
  - Limit implementation to local code changes only. Rejected because the user also asked for server-side embedding/model configuration.
