# ChainWatch

ChainWatch is a local-first retail risk intelligence platform for monitoring inventory pressure, fulfillment risk, and external disruptions that can affect product availability. It is designed for teams that need a practical operational view of what is happening to SKUs, suppliers, regions, and customer delivery commitments without depending on a cloud-heavy stack for the first version.

The v1 product is intentionally documentation-first. This repository begins with a complete project spec so implementation can proceed in a controlled way across frontend, backend, storage, data model, agent orchestration, and tasks tracking.

## Problem Statement

Retail teams often track demand, stock, supplier reliability, and shipping risk in separate tools. That makes it hard to answer simple operational questions:

- Which products are most likely to stock out in the next few days?
- Which supplier or country issue is putting the biggest revenue at risk?
- Which delays are caused by demand spikes versus external disruptions?
- Which products and regions should be escalated right now?

ChainWatch solves this by combining historical internal data with live external risk monitoring in one local-first system.

## Product Scope

ChainWatch is a retail inventory, fulfillment, and external-risk intelligence product. It is not a procurement workflow system and it is not a general analytics warehouse.

### Core capabilities

- Surface operational KPIs and active risk alerts on a dashboard.
- Answer grounded natural-language questions in a chat interface with citations.
- Highlight countries with active risk signals on a map.
- Generate structured local reports in JSON and Markdown.
- Show product-level demand, stock, supplier exposure, and fulfillment risk.
- Import local CSV data for sales, inventory, products, and suppliers.

## V1 Pages

- `Dashboard`
- `Chat`
- `Map`
- `Reports`
- `Product Detail`
- `Data Import/Settings`

Detailed page definitions live in [PAGES.md](PAGES.md).

## Backend Agent System

The backend centers on six coordinated components:

- `External Risk Agent`
- `Demand Agent`
- `Inventory Agent`
- `Fulfillment Agent`
- `Reporting Agent`
- `Chat Orchestrator`

Detailed responsibilities live in [AGENTS.md](AGENTS.md).

## Chosen Stack

### Frontend

- `Next.js` with App Router
- `TypeScript`
- `Tailwind CSS`
- `shadcn/ui` for reusable UI primitives
- `Recharts` for charts
- `React Simple Maps` for the country risk map

### Backend

- `Python`
- `FastAPI`
- `Pydantic`
- `sqlite3`
- Local filesystem storage for artifacts, logs, cache, and report output

### Report output

- `JSON + Markdown`

### Provider strategy

The LLM provider and external web-search provider are intentionally `TBD`. The architecture defines adapter boundaries so the final model and search services can be selected later without changing product behavior or page requirements.

## Local-First Philosophy

V1 should work entirely from the project directory with no required cloud infrastructure. The local runtime is expected to manage:

- Structured application data in `data/app.db`
- Imported source files in `data/imports/`
- Generated reports in `data/reports/json/` and `data/reports/markdown/`
- Cached external-risk responses in `data/cache/external_risk/`
- Logs and agent traces in `data/logs/`

## Documentation Map

- [CLAUDE.md](CLAUDE.md): AI collaborator rules and repo conventions
- [PRD.md](PRD.md): product intent and scope
- [PAGES.md](PAGES.md): page-by-page requirements
- [ARCHITECTURE.md](ARCHITECTURE.md): system design and data flow
- [AGENTS.md](AGENTS.md): agent roles and orchestration
- [DATA_MODEL.md](DATA_MODEL.md): sqlite schema and relationships
- [API_SPEC.md](API_SPEC.md): backend contract for frontend integration
- [tasks/STATUS.md](tasks/STATUS.md): lightweight Jira-style status board
- [tasks/FRONTEND_TASKS.md](tasks/FRONTEND_TASKS.md): frontend build steps
- [tasks/BACKEND_TASKS.md](tasks/BACKEND_TASKS.md): backend build steps
- [tasks/DECISIONS.md](tasks/DECISIONS.md): decision log
- [tasks/ISSUES.md](tasks/ISSUES.md): issue tracker

## Current Implementation Status

Phase 1 backend foundation is now implemented under `backend/`.

Included in the current codebase:

- FastAPI backend scaffold
- Typed runtime settings
- sqlite bootstrap and repository helpers
- Managed local storage bootstrap under `data/`
- CSV import pipeline for suppliers, products, sales, inventory, and fulfillment
- local demo seed workflow for development data
- core external-risk, demand, inventory, and fulfillment agent implementations
- sqlite-backed agent run traces and local run logs
- baseline `GET /api/health`
- backend `pytest` coverage for foundation, imports, seed, and agent flows

## Backend Quickstart

From the repository root:

```bash
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

Health check:

```text
GET /api/health
```

Import demo data:

```bash
cd backend
uv run python -m app.seed
```

## Planned Repository Shape

```text
ChainWatch/
├── README.md
├── CLAUDE.md
├── PRD.md
├── PAGES.md
├── ARCHITECTURE.md
├── AGENTS.md
├── DATA_MODEL.md
├── API_SPEC.md
├── frontend/
├── backend/
├── data/
└── tasks/
```

The `frontend/` directory remains a planned implementation target. The `backend/` project now exists, and the `data/` directory is created as a managed runtime location by the backend bootstrap flow.
The backend API surface is now live for health, dashboard, map, products, chat, reports, and imports, and phase-6 reliability work adds freshness metadata, background report generation, and a regression checklist.

## Implementation Order

1. Lock repository conventions and task workflow.
2. Build backend structure, sqlite schema, and local storage layout.
3. Add import pipeline and seed data.
4. Implement risk-analysis agents, report generation, and chat orchestration.
5. Expose the remaining REST APIs for dashboard, chat, map, products, reports, and imports.
6. Build the frontend pages and shared UI/data layers.
7. Add verification, eval scenarios, and documentation updates.

The detailed step plan is tracked in `tasks/FRONTEND_TASKS.md` and `tasks/BACKEND_TASKS.md`.
