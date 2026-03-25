# fuseAgent Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-22

## Active Technologies
- Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, Pydantic, existing agent WebSocket chat stack, existing search and graph services, Next.js 15, next-intl, Tailwind CSS 4, `react-force-graph-2d`, framer-motion, reused MiroFish graph visual patterns (003-answer-graph-sources)
- PostgreSQL chat/search metadata, collection config JSON, existing vector/fulltext stores, LightRAG graph storage, Neo4j-backed MiroFish graph storage (003-answer-graph-sources)
- Python 3.11 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, Pydantic, existing WebSocket chat flow, Next.js 15, next-intl, Tailwind CSS 4, Mermaid, panzoom, existing ApeRAG drawer/chat components (004-answer-topology-sources)
- Existing chat history/reference payload storage in PostgreSQL plus current document metadata carried inside `Reference.metadata` (004-answer-topology-sources)

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
- 004-answer-topology-sources: Added Python 3.11 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, Pydantic, existing WebSocket chat flow, Next.js 15, next-intl, Tailwind CSS 4, Mermaid, panzoom, existing ApeRAG drawer/chat components
- 003-answer-graph-sources: Added Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend + FastAPI, Pydantic, existing agent WebSocket chat stack, existing search and graph services, Next.js 15, next-intl, Tailwind CSS 4, `react-force-graph-2d`, framer-motion, reused MiroFish graph visual patterns

- 001-aperag-home-adapt: Added Python 3.11.12 backend, TypeScript 5 / React 19 / Next.js 15 frontend + ApeRAG backend stack, Celery, SQLAlchemy/FastAPI-adjacent service layer, Next.js 15, next-intl, Tailwind CSS 4, Radix UI

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
