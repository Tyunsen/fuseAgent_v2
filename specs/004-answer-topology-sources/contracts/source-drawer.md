# Contract: Source Drawer

## Scope

This contract defines the user-visible behavior of answer sources for this
increment.

## Contract

1. The answer continues to expose sources through the existing ApeRAG-style source entry and drawer behavior.
2. The drawer body shows one row per supporting source passage.
3. Each row includes document identity and the best trustworthy source locator available.
4. Each row can be expanded and collapsed independently.
5. Expanding a row reveals the supporting passage within the drawer.
6. When exact paragraph precision is unavailable, the row explicitly communicates that the locator is approximate.
