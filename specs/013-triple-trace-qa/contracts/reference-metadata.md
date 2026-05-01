# Contract: Reference Metadata For Trace Support

## Scope

This contract defines the evidence identity and locator fields that trace-mode
answers and conclusion bindings rely on.

## Contract

1. Every answer source row used by trace support MUST preserve a stable `source_row_id`.
2. Every source row MUST retain document identity through existing metadata such as `document_id` and `document_name`.
3. The best trustworthy locator available MUST remain available through existing metadata such as page hints, markdown/pdf source maps, titles, or chunk IDs.
4. The citation layer MUST reuse the current `paragraph_precise` signal, or an equivalent derived flag, to distinguish exact locators from approximate ones.
5. Conclusion bindings MUST reference existing `source_row_id` values rather than inventing a new parallel evidence identifier.
6. If exact fragment precision is unavailable, the UI MUST display the locator as approximate instead of implying false precision.
7. Trace-mode support generation MAY enrich presentation labels, but it MUST NOT overwrite or sever the original document-fragment linkage already carried by current reference metadata.
