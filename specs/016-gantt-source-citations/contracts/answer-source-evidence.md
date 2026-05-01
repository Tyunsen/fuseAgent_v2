# Contract: Answer Source Evidence

## Scope

Defines the required UI contract for source access and inline citation markers in QA answers.

## Contract

1. If an answer has source-backed evidence, the message action row MUST include a single source entry labeled `参考文档来源` (localized equivalent allowed).
2. The source entry MUST appear in the same action area as feedback/copy-style controls, not as a separate content block below the answer body.
3. Activating the source entry MUST open a right-side drawer that lists all answer-local source rows.
4. The bottom collapsed source card pattern MUST NOT remain visible once the drawer contract is active.
5. Answer prose that uses evidence MUST display inline citation markers in the format `[n]`.
6. Each inline citation marker `[n]` MUST correspond to the same numbered source row shown in the drawer.
7. Answers without usable source rows MUST show neither fake inline citation markers nor a fake source action entry.
