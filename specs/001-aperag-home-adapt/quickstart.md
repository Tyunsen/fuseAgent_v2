# Quickstart: ApeRAG-Style Knowledge Base Homepage

## Local Validation

1. Copy ApeRAG into the repo and install dependencies:

```powershell
cd E:\codes\fuseAgent_v2\fuseAgent
uv sync
cd web
yarn install
```

2. Prepare env files:

```powershell
Copy-Item .\envs\env.template .\.env
Copy-Item .\web\deploy\env.local.template .\web\.env
```

3. Ensure the frontend default locale is Chinese and the root route goes directly into the workspace collections flow.

4. Start the backend and frontend using the inherited ApeRAG development workflow.

5. Validate these behaviors:
  - Visiting `/` no longer shows the marketing page.
  - Unauthenticated access is redirected to sign-in.
  - After sign-in, the first working destination is `/workspace/collections`.
  - The right-top area shows only the user menu.
  - Homepage labels default to Chinese.
  - Each collection entry exposes document management and Q&A/search actions.
  - Creating a collection with the reused full form returns the new collection to the homepage list.

## Server Validation

1. Deploy the repo under `/home/common/jyzhu/ucml`.
2. Reuse the inherited Docker or direct-run ApeRAG stack.
3. Configure backend/frontend env files without committing secrets.
4. Put the embedding worker on an idle GPU if one is available.
5. Verify the same route and UI behaviors against the remote deployment.
6. Create a local port-forward script that maps the remote service port to an unused local port.

## Smoke Checklist

- Sign-in works and routes into the knowledge base homepage.
- The homepage shows list/search/create.
- Document management opens for a selected collection.
- Q&A/search opens for a selected collection.
- First-build collections cannot perform Q&A.
- Collections under incremental update show a stale-results warning.
