# CLAUDE.md

This file defines how AI collaborators should work in the ChainWatch repository.

## Mission

Build ChainWatch as a local-first retail risk intelligence product for inventory, fulfillment, and external-risk monitoring. The repository should remain documentation-driven and implementation should follow the task system in `tasks/`.

## Non-Negotiable Stack

Do not change the core stack for v1 unless `tasks/DECISIONS.md` is updated first.

### Frontend

- `Next.js` App Router
- `TypeScript`
- `Tailwind CSS`
- `shadcn/ui`
- `Recharts`
- `React Simple Maps`

### Backend

- `Python`
- `FastAPI`
- `Pydantic`
- `sqlite3`
- Local filesystem storage inside the project

### Output and storage

- Reports must be generated as `JSON + Markdown`
- Structured data must live in sqlite
- Files, cache, logs, and artifacts must stay under the project directory

## Product Boundaries

- ChainWatch is a retail operations product, not a procurement or ERP replacement.
- V1 is local-first and should not require Azure, AWS, GCP, or managed databases.
- The LLM and web-search providers are intentionally abstract. Keep provider-specific logic behind adapters.
- Do not introduce agent frameworks by default. Prefer a simple, debuggable orchestration layer in Python.

## Documentation Discipline

When behavior changes, update the relevant docs in the same task:

- `PRD.md` for product scope changes
- `PAGES.md` for page behavior changes
- `ARCHITECTURE.md` for system design changes
- `AGENTS.md` for agent responsibility changes
- `DATA_MODEL.md` for schema changes
- `API_SPEC.md` for backend contract changes
- `tasks/STATUS.md` whenever task state changes
- `tasks/DECISIONS.md` whenever a meaningful implementation decision is made

Do not let code drift away from the docs.

## Task Workflow

- Every implementation task must map to a task ID from `tasks/FRONTEND_TASKS.md` or `tasks/BACKEND_TASKS.md`.
- `tasks/STATUS.md` is the source of truth for `Todo`, `In Progress`, `Blocked`, and `Done`.
- Move a task into `In Progress` before major work starts.
- Move a task into `Done` only after acceptance criteria are met and the related docs are updated.
- If a task needs a new dependency or changes scope, record it in `tasks/DECISIONS.md`.

## Coding Conventions

- Prefer ASCII unless the file already uses non-ASCII.
- Use descriptive names over abbreviations.
- Keep modules small and responsibility-focused.
- Favor explicit data models over loose dictionaries in backend code.
- Keep frontend components composable and route-aware.
- Avoid hidden magic in agent orchestration. Every agent step should be traceable.

## Architecture Guardrails

- Frontend should call the backend through documented REST APIs only.
- Do not duplicate business logic in the frontend.
- SQLite is the source of truth for structured operational data.
- Generated files belong in `data/`, not in source directories.
- External risk fetches must support caching and stale-data behavior.
- Chat responses must preserve citation metadata for UI rendering and reports.
- Product pages, dashboard views, reports, and chat answers must all derive from the same backend data model.

## Naming Conventions

- Use `snake_case` in Python modules and data-layer utility names.
- Use `PascalCase` for React components.
- Use `camelCase` for TypeScript variables, props, and client-side helpers.
- Use singular table names only if the entire schema follows singular naming. For this project, use plural table names consistently.
- Use uppercase task IDs such as `FE-01` and `BE-01`.

## Local Data Layout

Planned project-managed directories:

- `data/app.db`
- `data/imports/raw/`
- `data/imports/processed/`
- `data/reports/json/`
- `data/reports/markdown/`
- `data/cache/external_risk/`
- `data/logs/app/`
- `data/logs/agent_runs/`

## Provider Adapters

Keep the following interfaces provider-agnostic:

- `LLM client`
- `Web search client`
- `Citation formatter`
- `Report renderer`

If a provider is selected later, add the concrete adapter behind the abstract interface rather than spreading provider logic throughout the codebase.

## Quality Bar

Before closing a task:

- Verify the task acceptance criteria.
- Verify the docs still agree with the implementation.
- Verify `tasks/STATUS.md` reflects the new state.
- Record any important tradeoff in `tasks/DECISIONS.md`.

## What To Avoid

- Cloud-only assumptions
- Hidden state outside the repository
- Untracked schema changes
- Large undocumented prompt strings scattered across files
- UI states that are unsupported by backend contracts
- Agent decisions that cannot be inspected or explained
