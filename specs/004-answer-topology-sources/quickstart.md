# Quickstart: ApeRAG Answer Topology And Sources

1. Open the local app and sign in with a valid account.
2. Open an existing chat answer that contains a Mermaid `流程拓扑` block and one or more sources.
3. Confirm the answer no longer shows the extra inline `Knowledge Graph` support block from the previous 003 implementation.
4. Confirm the answer footer still exposes sources through the ApeRAG-style source entry.
5. Open the source drawer and verify:
   - one row appears per source passage
   - rows can be expanded and collapsed
   - each row shows document identity and a source locator
   - approximate locators are clearly labeled when exact precision is unavailable
6. Confirm the `流程拓扑` graph still renders from the answer content and visually looks closer to the MiroFish reference.
7. Switch the topology block to its raw data view and confirm the raw Mermaid data remains accessible.
8. Run targeted backend verification plus frontend lint/build before closing the feature.
