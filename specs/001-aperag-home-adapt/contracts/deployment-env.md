# Contract: Deployment Environment

## Server Placement

- Target host: user-provided Linux server
- Allowed project base path: `/home/common/jyzhu/ucml`
- Deployment MUST remain inside that directory tree.

## Runtime Secrets

- LLM API keys and similar credentials MUST be injected through env files or server-side runtime configuration.
- Supplied secrets MUST NOT be committed into repository files.

## Required Runtime Configuration

- Backend services:
  - PostgreSQL
  - Redis
  - Vector store
  - Search/index dependencies inherited from ApeRAG
- Frontend services:
  - Next.js web app with default locale `zh-CN`
- Worker services:
  - Embedding/model worker placed on an idle GPU when possible

## Port Forwarding

- After remote deployment, provide a local script that forwards the remote service port to an unused local port.

## Product Adaptation Constraints

- Deployment assets may be adapted from ApeRAG, but resulting runtime behavior must satisfy:
  - No marketing homepage
  - Chinese-first homepage
  - Direct knowledge base work entry
  - Top-right user menu only
