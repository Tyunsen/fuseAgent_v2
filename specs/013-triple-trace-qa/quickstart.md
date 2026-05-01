# Quickstart: Knowledge Base Triple Trace QA

1. Prepare a knowledge base whose collection metadata includes a meaningful description or title and whose documents contain explicit dates, periods, locations, and named entities.
2. Trigger or rerun graph extraction for that collection and confirm ontology generation now keeps the fixed broad base types, adds lightweight knowledge-base-specific supplemental types, and preserves evidence-backed time/place attributes on extracted entities or relationships when present.
3. Open the chat page for that collection and verify the input area exposes four answer modes: `default`, `time`, `space`, and `entity`.
4. Ask the same question once in `default` mode and confirm the current answer behavior remains available with mixed retrieval and no trace-specific restructuring forced on the user.
5. Ask a time-oriented question such as "3月发生了什么事情？" in `time` mode and verify:
   - the system interprets the month into a normalized time window
   - the answer is organized by time rather than as a plain summary
   - major conclusions show visible source binding
   - the graph is time-oriented rather than the default topology view
6. Ask a space-oriented question such as "阿布扎比发生了什么？" in `space` mode and verify:
   - place wording is normalized for retrieval
   - the answer is organized around the location
   - citations still point to concrete source rows
   - the graph is grouped or centered by place
7. Ask an entity-oriented question such as "伊朗相关的关键动作有哪些？" in `entity` mode and verify:
   - the system identifies the focal entity
   - the answer is organized around that entity and its related evidence
   - the graph is centered on the focal entity and relevant neighbors
8. Open visible citations for multiple conclusions and confirm each one resolves to the current answer's source drawer or evidence view with document identity and the best trustworthy locator, explicitly marking approximate locators when needed.
9. Run targeted backend verification plus frontend checks:
   - `pytest` for ontology, extraction, trace-support, and citation binding changes
   - `corepack yarn lint`
   - `corepack yarn build`
10. Regenerate `web/build`, restart the affected runtime stack, and verify the remote deployment through the forwarded frontend and API ports before closing the feature.
