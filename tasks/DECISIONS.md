# DECISIONS

This file is the running decision log for ChainWatch. Record meaningful implementation or scope decisions here so the repository has a permanent explanation for why a change was made.

## Decision Template

| Date | ID | Decision | Rationale | Impact |
| --- | --- | --- | --- | --- |
| YYYY-MM-DD | DEC-00 | Short title | Why this was chosen | What changes because of it |

## Seed Decisions

| Date | ID | Decision | Rationale | Impact |
| --- | --- | --- | --- | --- |
| 2026-04-23 | DEC-01 | Use `ChainWatch` as the project name | The name is broad enough for supply-chain and retail risk use without copying the inspiration project name | All docs, routes, and artifacts use `ChainWatch` branding |
| 2026-04-23 | DEC-02 | Keep the product local-first for v1 | Local runtime is the fastest way to build and validate the workflow without cloud setup overhead | SQLite and local filesystem storage are first-class design constraints |
| 2026-04-23 | DEC-03 | Use `Next.js + TypeScript + Tailwind CSS` on the frontend | This stack supports fast page development with strong typing and a modern React app structure | Frontend docs and tasks assume App Router and typed API consumers |
| 2026-04-23 | DEC-04 | Use `Python + FastAPI + Pydantic + sqlite3` on the backend | The stack is simple, local-friendly, and well suited to API-first agent orchestration | Backend docs and tasks assume REST endpoints and sqlite-backed persistence |
| 2026-04-23 | DEC-05 | Use `React Simple Maps` for the v1 map | Country-level issue highlighting is enough for the MVP and this approach keeps mapping complexity low | The Map page is documented as a country risk view, not a geospatial routing tool |
| 2026-04-23 | DEC-06 | Generate reports as `JSON + Markdown` | These formats are easy to inspect locally, easy to diff, and require no heavy export tooling in v1 | Reports page and reporting flow assume local artifact paths for JSON and Markdown |
| 2026-04-23 | DEC-07 | Keep LLM and search providers abstract for now | The final provider choice has not been made yet and should not force architecture churn | Adapter interfaces must exist before provider-specific implementations are added |
| 2026-04-23 | DEC-08 | Use a lightweight custom orchestration layer instead of a heavy agent framework | The MVP needs transparency and predictable debugging more than framework breadth | `AGENTS.md` and backend tasks assume explicit orchestration and traceable agent runs |
| 2026-04-23 | DEC-09 | Demand analysis must use `3-5 years` of sales history | Demand seasonality and spike detection are core to the retail use case | `sales_history`, Product Detail, Dashboard, and Demand Agent logic all assume multi-year history |
| 2026-05-01 | DEC-10 | Use `uv + pyproject.toml` for backend dependency management | The backend now needs a reproducible local workflow with typed metadata and a clean Python toolchain | The backend ships as an isolated Python project under `backend/` with documented install and test commands |
| 2026-05-01 | DEC-11 | Target Python `3.12` for backend development | FastAPI and Pydantic v2 work well on Python `3.12`, and the phase-1 plan explicitly targets it | Local backend setup uses a Python `3.12` virtual environment |
| 2026-05-01 | DEC-12 | Bootstrap sqlite from a checked-in schema file during app startup | The project needs deterministic local setup without introducing migration tooling in phase 1 | `backend/app/db/schema.sql` is applied idempotently at startup to create the documented tables and indexes |
| 2026-05-01 | DEC-13 | Use stdlib `sqlite3` with a thin repository layer and no ORM or Alembic in phase 1 | The MVP favors traceability and explicit SQL over abstraction-heavy persistence layers | Data access stays close to the documented schema and avoids migration or ORM overhead in the foundation slice |
| 2026-05-01 | DEC-14 | Auto-create managed runtime directories under `data/` on backend startup | Local-first startup should work from a clean checkout without manual directory prep | The backend startup flow provisions runtime storage for the database, imports, reports, cache, and logs before serving requests |
