# ChainWatch

> Local-first retail risk intelligence — monitor inventory pressure, fulfillment risk, and supply chain disruptions without a cloud-heavy stack.

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![Next.js](https://img.shields.io/badge/Next.js-App_Router-black) ![FastAPI](https://img.shields.io/badge/FastAPI-backend-green) ![SQLite](https://img.shields.io/badge/Storage-SQLite-lightgrey)

---

## What is ChainWatch?

Retail teams track demand, stock, supplier reliability, and shipping risk in separate tools — making it hard to answer simple operational questions fast.

ChainWatch brings it all together in one local-first system:

- **Which products are most likely to stock out in the next few days?**
- **Which supplier or regional issue is putting the biggest revenue at risk?**
- **Which delays are caused by demand spikes vs. external disruptions?**
- **Which products and regions need escalation right now?**

---

## Features

- 📊 **Dashboard** — Operational KPIs and active risk alerts at a glance
- 💬 **Chat** — Grounded natural-language Q&A with citations
- 🗺️ **Map** — Country-level risk signals visualized
- 📄 **Reports** — Structured JSON and Markdown report generation
- 📦 **Product Detail** — Demand, stock, supplier exposure, and fulfillment risk per SKU
- 📥 **Data Import** — CSV import for sales, inventory, products, and suppliers

---

## Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS, React Simple Maps |
| Backend | Python, FastAPI, Pydantic |
| Storage | SQLite (`data/app.db`), local filesystem |
| Reports | JSON + Markdown |
| LLM | Configurable (OpenAI adapter included) |
| Web Search | Configurable (Exa adapter included) |

---

## Quickstart

### Backend

```bash
cd backend
uv sync --extra dev
uv run uvicorn app.main:app --reload
```

Health check: `GET /api/health`

Seed demo data:
```bash
uv run python -m app.seed
```

> **Note:** External risk events require live search configured or cached data. Report browsing in-app is not yet supported — generation only.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend expects the backend at `http://127.0.0.1:8000/api` by default. Override with `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local`.

---

## Project Structure

```
ChainWatch/
├── README.md
├── CLAUDE.md           # AI collaborator rules and repo conventions
├── PRD.md              # Product intent and scope
├── PAGES.md            # Page-by-page requirements
├── ARCHITECTURE.md     # System design and data flow
├── AGENTS.md           # Agent roles and orchestration
├── DATA_MODEL.md       # SQLite schema and relationships
├── API_SPEC.md         # Backend contract for frontend integration
├── frontend/           # Next.js App Router project
├── backend/            # FastAPI backend
├── data/               # Runtime data (db, imports, reports, cache, logs)
└── tasks/
    ├── STATUS.md        # Lightweight status board
    ├── FRONTEND_TASKS.md
    ├── BACKEND_TASKS.md
    ├── DECISIONS.md     # Decision log
    └── ISSUES.md        # Issue tracker
```

---

## Agent System

The backend coordinates six agents:

| Agent | Responsibility |
|---|---|
| External Risk Agent | Monitors live supply chain disruptions |
| Demand Agent | Tracks and forecasts product demand |
| Inventory Agent | Monitors stock levels and pressure |
| Fulfillment Agent | Tracks delivery commitments and risk |
| Reporting Agent | Generates structured reports |
| Chat Orchestrator | Routes and grounds natural-language queries |

External risk lookups are cached locally per UTC day — dashboard, map, chat, and product pages reuse cached data instead of repeated API calls.

---

## Local-First Philosophy

V1 runs entirely from the project directory — no cloud infrastructure required.

| Path | Purpose |
|---|---|
| `data/app.db` | Application database |
| `data/imports/` | Uploaded source files |
| `data/reports/` | Generated JSON and Markdown reports |
| `data/cache/external_risk/` | Cached external risk responses |
| `data/logs/` | Agent traces and run logs |

---

## Current Status

**Backend** — All phases complete:
- FastAPI scaffold, SQLite schema, local storage bootstrap
- CSV import pipeline (suppliers, products, sales, inventory, fulfillment)
- Demo seed workflow
- All agents implemented (risk, demand, inventory, fulfillment, reporting, chat)
- Full REST API surface (health, dashboard, map, products, chat, reports, imports)
- pytest coverage across reliability and scenario tests

**Frontend** — All phases complete:
- Next.js App Router scaffold with Stitch-aligned shell
- Live Dashboard, Map, and Product Detail pages
- Live Chat, Reports, and Settings/Import workflows
- Shared API client, response typings, and UI state components

---

## License

MIT