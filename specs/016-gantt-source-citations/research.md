# Research: Gantt Source Citations

## Decision 1: Fix Time Mode Inside Existing Trace-Support Flow

- **Decision**: Improve time-mode event labels and time placement inside the current `trace_support_service -> answer_graph_service -> message-answer-graph` path.
- **Rationale**: The system already computes structured conclusions and grouped graph payloads. The defect is quality of labels and dates, not absence of a gantt pipeline.
- **Alternatives considered**:
  - Build a separate gantt-only backend DTO: rejected because it duplicates the existing answer-support graph contract.
  - Parse gantt tasks only from LLM answer text: rejected because it is less stable and was the main source of incorrect `graph TD` fallback behavior.

## Decision 2: Time Mode Should Not Render Secondary Group Cards

- **Decision**: Suppress the extra grouped-card section below the gantt in time mode.
- **Rationale**: The feature requires only one main time graph for the time-trace shell. The secondary cards duplicate information and visually conflict with the main gantt.
- **Alternatives considered**:
  - Keep the grouped cards as a secondary navigation aid: rejected because the user explicitly does not want them.
  - Replace them with another summary panel: rejected because it would reintroduce duplicate support cards.

## Decision 3: Source Access Moves To The Message Action Bar

- **Decision**: Put the source entry in the message action row beside feedback/copy and open a right-side drawer.
- **Rationale**: The chat UI already has message-scoped actions and an existing drawer pattern. This keeps the answer body clean and makes source access feel like a message action rather than a second content block.
- **Alternatives considered**:
  - Keep the bottom collapsed source card: rejected because it is too far from the action zone and duplicates support content under the answer.
  - Add a top-right source trigger inside the card header: rejected because it fragments the message action model and is less consistent than the shared action row.

## Decision 4: Inline Citations Should Be View-Layer Numbering, Not New Persistence

- **Decision**: Generate `[n]` inline citation markers from the prepared reference row order in the chat render path.
- **Rationale**: The existing reference rows already define stable answer-local evidence items. Reusing their order avoids new persistence or backend numbering APIs.
- **Alternatives considered**:
  - Persist citation indices in message history: rejected because the feature only needs stable per-render numbering, not a new storage contract.
  - Ask the model to generate citation numbers itself: rejected because it is less reliable and can drift from the actual displayed source rows.

## Decision 5: Strip Naked Mermaid Text Defensively

- **Decision**: Extend answer-body sanitization to remove naked Mermaid directives such as `graph TD`, `flowchart`, or `gantt` even when they are not wrapped in fenced code blocks.
- **Rationale**: Prompt guidance reduces bad output but does not eliminate it. A UI-layer sanitizer prevents raw graph syntax from leaking into the visible answer body.
- **Alternatives considered**:
  - Depend only on prompt guidance: rejected because the bug already demonstrated prompt non-compliance.
  - Hide all lines with brackets/arrows heuristically: rejected because it would be too aggressive and risk damaging legitimate prose.
