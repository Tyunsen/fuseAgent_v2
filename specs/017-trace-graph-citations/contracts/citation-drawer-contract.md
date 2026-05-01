# Contract: Citation Drawer Interaction

## Scope

Defines the answer-body citation and source-drawer interaction contract for all cited QA modes.

## Required Rendering

- The answer body must contain inline `[n]` citation markers at the actual cited sentence positions.
- The answer-card header must not show a detached `[1][2][3]...` citation strip.
- The action row must expose a `参考文档来源` entry that opens the same right-side drawer.

## Required Interaction

- Clicking an inline `[n]` marker must:
  - open the right-side `参考文档来源` drawer
  - focus the matching numbered source row
  - keep the drawer numbering aligned with the inline citation numbering
- Clicking the action-row `参考文档来源` entry must open the same drawer without losing numbering consistency.
- Clicking graph elements may also focus rows, but must reuse the same drawer/focus state.

## Invalid Behavior

- plain-text `[n]` markers that cannot be clicked
- a detached citation-number cluster in the answer header
- drawer numbering that does not match inline numbering
- fake citation markers when no actual reference row is bound
