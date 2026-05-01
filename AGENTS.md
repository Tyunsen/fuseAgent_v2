# fuseAgent Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-05

## Active Technologies
- Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, Pydantic, existing agent WebSocket chat stack, existing search and graph services, Next.js 15, next-intl, Tailwind CSS 4, `react-force-graph-2d`, framer-motion, reused MiroFish graph visual patterns (003-answer-graph-sources)
- PostgreSQL chat/search metadata, collection config JSON, existing vector/fulltext stores, LightRAG graph storage, Neo4j-backed MiroFish graph storage (003-answer-graph-sources)
- Python 3.11 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, Pydantic, existing WebSocket chat flow, Next.js 15, next-intl, Tailwind CSS 4, Mermaid, panzoom, existing ApeRAG drawer/chat components (004-answer-topology-sources)
- Existing chat history/reference payload storage in PostgreSQL plus current document metadata carried inside `Reference.metadata` (004-answer-topology-sources)
- Python 3.11.12 + FastAPI, Celery, SQLAlchemy, existing ApeRAG document lifecycle services, existing MiroFish graph extraction stack, Neo4j driver, Pydantic models (005-incremental-graph-update)
- PostgreSQL for collection/document metadata, object storage for parsed document markdown, Neo4j for MiroFish graphs, collection config JSON in `collection.config` (005-incremental-graph-update)
- Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, Pydantic, existing ApeRAG collection/document services, existing MiroFish graph lifecycle service, Next.js 15, next-intl, Tailwind CSS 4, Radix UI (006-index-status-visibility)
- Existing PostgreSQL collection/document/index metadata, object storage for parsed markdown, Neo4j-backed MiroFish graph metadata (006-index-status-visibility)
- Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, existing ApeRAG document upload/confirm APIs, existing MiroFish graph lifecycle helpers, Next.js 15, next-intl, Tailwind CSS 4 (007-auto-upload-build)
- Existing PostgreSQL document metadata, object storage for uploaded files, Neo4j-backed MiroFish graph metadata (007-auto-upload-build)
- Python 3.11.12 + FastAPI service layer, SQLAlchemy-backed `db_ops`, existing `EmbeddingService`, existing VECTOR indexer flow (008-fix-vector-index)
- PostgreSQL-backed provider and collection metadata plus existing vector store adapters (008-fix-vector-index)
- Python 3.11.12 + FastAPI service layer, SQLAlchemy-backed `db_ops`, existing Celery task flow, existing MiroFish graph lifecycle service, Neo4j-backed graph backend (009-mirofish-build-speed)
- PostgreSQL collection/document metadata, object storage cached markdown, Neo4j graph storage (009-mirofish-build-speed)
- TypeScript 5 / React 19 / Next.js 15 frontend within the existing full-stack application + existing ApeRAG upload/confirm APIs, existing MiroFish collection detection helpers, `next/navigation`, `next-intl`, existing `Alert` UI component (010-upload-completion-ux)
- Existing PostgreSQL-backed document metadata and current collection config state; no new persistence (010-upload-completion-ux)
- Python 3.11.12 + FastAPI service layer, SQLAlchemy-backed `db_ops`, Celery task flow, existing MiroFish graph lifecycle service, Pydantic settings (011-fix-graph-build-slow)
- PostgreSQL collection/document metadata, object storage cached markdown, Neo4j graph storage, Redis-backed Celery broker (011-fix-graph-build-slow)
- Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, Pydantic, SQLAlchemy-backed services, existing WebSocket chat flow, existing collection search flow, existing MiroFish graph extraction stack, existing answer graph service, Next.js 15, next-intl, Tailwind CSS 4, `react-force-graph-2d`, Mermaid (013-triple-trace-qa)
- PostgreSQL metadata, existing vector store, Elasticsearch fulltext index, LightRAG graph/search artifacts, Neo4j-backed MiroFish graph data, existing reference metadata carried in `Reference.metadata` (013-triple-trace-qa)
- Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, Pydantic, SQLAlchemy-backed services, existing WebSocket chat flow, existing trace-support service, existing answer graph service, Next.js 15, next-intl, Tailwind CSS 4, `react-force-graph-2d`, Mermaid (015-qa-mode-display)
- PostgreSQL metadata, existing vector store, Elasticsearch fulltext index, Neo4j-backed MiroFish graph data, existing `Reference.metadata` for answer source binding (015-qa-mode-display)
- Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, Pydantic, SQLAlchemy-backed services, existing WebSocket chat flow, existing trace-support service, existing answer graph service, Next.js 15, next-intl, Tailwind CSS 4, Mermaid, existing drawer UI primitives, `react-force-graph-2d` (016-gantt-source-citations)
- PostgreSQL metadata, existing vector store, Elasticsearch fulltext index, Neo4j-backed MiroFish graph data, existing `Reference.metadata`, existing stored chat message history (016-gantt-source-citations)
- Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, Pydantic, SQLAlchemy-backed services, existing WebSocket chat flow, existing trace-support service, existing answer graph service, existing chat markdown renderer, Next.js 15, next-intl, Tailwind CSS 4, Mermaid, `react-force-graph-2d` (017-trace-graph-citations)
- PostgreSQL metadata, existing vector store, Elasticsearch fulltext index, Neo4j-backed MiroFish graph data, existing `Reference.metadata`, existing chat history storage (017-trace-graph-citations)

- Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend + ApeRAG backend stack, Celery, SQLAlchemy/FastAPI-adjacent service layer, Next.js 15, next-intl, Tailwind CSS 4, Radix UI (001-aperag-home-adapt)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend: Follow standard conventions

## Recent Changes
- 017-trace-graph-citations: Added Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, Pydantic, SQLAlchemy-backed services, existing WebSocket chat flow, existing trace-support service, existing answer graph service, existing chat markdown renderer, Next.js 15, next-intl, Tailwind CSS 4, Mermaid, `react-force-graph-2d`
- 016-gantt-source-citations: Added Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, Pydantic, SQLAlchemy-backed services, existing WebSocket chat flow, existing trace-support service, existing answer graph service, Next.js 15, next-intl, Tailwind CSS 4, Mermaid, existing drawer UI primitives, `react-force-graph-2d`
- 015-qa-mode-display: Added Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, Pydantic, SQLAlchemy-backed services, existing WebSocket chat flow, existing trace-support service, existing answer graph service, Next.js 15, next-intl, Tailwind CSS 4, `react-force-graph-2d`, Mermaid


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
