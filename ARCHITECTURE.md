# ARCHITECTURE

## System Goal

ChainWatch is a local-first retail risk intelligence application. The architecture must support:

- historical retail data analysis,
- external-risk monitoring with citations,
- explainable agent outputs,
- local report generation,
- and a frontend that consumes a stable REST API contract.

## High-Level Design

```text
Next.js frontend
    |
    v
FastAPI backend
    |
    +--> sqlite3 database
    +--> local filesystem storage
    +--> provider-agnostic LLM adapter
    +--> provider-agnostic web-search adapter
```

## Frontend Responsibilities

The frontend is responsible for presentation, navigation, user interaction, and rendering backend results. It must not hold source-of-truth business logic.

### Core frontend responsibilities

- Render app shell and page layouts
- Fetch and display API data
- Manage local UI state, filters, and pending interactions
- Render charts, tables, map states, and citations
- Launch report generation and import actions
- Preserve contextual navigation between dashboard, map, product, chat, and reports

## Backend Responsibilities

The backend is responsible for data normalization, persistence, agent orchestration, risk scoring, and report generation.

### Core backend responsibilities

- Persist structured data in sqlite
- Store files and generated artifacts locally
- Normalize imported CSV content
- Orchestrate risk-analysis agents
- Query provider adapters for LLM and web-search capabilities
- Cache external-risk fetches
- Serve REST endpoints for all frontend pages
- Generate JSON and Markdown reports

## API Boundary

The frontend must only communicate with the backend through documented REST endpoints. API responses should include enough metadata for the UI to show:

- freshness
- severity
- scope
- citations
- report status
- error messages

No page should depend on direct sqlite access or filesystem reads from the browser.

## Local Storage Strategy

### SQLite

Structured operational data lives in `data/app.db`.

Primary responsibilities:

- products and suppliers
- inventory and sales history
- fulfillment status snapshots
- external risk events and country scores
- chat sessions and messages
- report metadata
- import runs
- agent run traces

### Filesystem storage

Generated and imported files live under project-managed directories:

```text
data/
├── app.db
├── imports/
│   ├── raw/
│   └── processed/
├── reports/
│   ├── json/
│   └── markdown/
├── cache/
│   └── external_risk/
└── logs/
    ├── app/
    └── agent_runs/
```

Use cases:

- Keep original uploaded CSV files in `imports/raw/`
- Keep normalized or enriched import artifacts in `imports/processed/`
- Store final report artifacts separately from metadata
- Cache external-risk responses so map and report generation remain predictable
- Save application logs and agent traces locally for debugging

## Provider Abstraction

Two backend interfaces must stay abstract:

- `LLMAdapter`
- `SearchAdapter`

The adapter layer hides provider-specific request/response details. The rest of the application should consume normalized internal models such as:

- `SearchResult`
- `Citation`
- `ChatCompletion`
- `StructuredRiskSummary`

This keeps the MVP stable while the exact providers remain undecided.

## Risk-Analysis Flow

### Input sources

- Imported product catalog data
- Imported supplier data
- Imported inventory snapshots
- Imported sales history with `3-5 years` of records
- Optional fulfillment performance snapshots
- Search-backed external disruption results

### Analysis pipeline

1. Import pipeline validates and stores raw files.
2. Import normalization writes structured rows into sqlite.
3. Backend pages and scheduled triggers invoke specialized agents.
4. Agents produce structured findings and write trace metadata.
5. API endpoints return consolidated page-specific responses.
6. Reporting Agent serializes risk summaries to JSON and Markdown.

## Agent Orchestration Model

The backend uses a lightweight orchestration layer rather than a heavy agent framework. The orchestrator should:

- decide which agent or agents are relevant,
- pass normalized context to each agent,
- merge the outputs into a stable response shape,
- preserve citation and trace metadata,
- and degrade gracefully when one source fails.

Examples:

- Dashboard summary can use precomputed aggregates plus cached external-risk summaries.
- Product detail can call Demand, Inventory, and Fulfillment agents with a single product scope.
- Chat can route to one or more agents depending on the question.
- Reports can call the same agents as page views, then serialize the result.

## Caching And Background Work

### External-risk cache

- External-risk search responses should be cached on disk.
- A cache entry older than `6 hours` is considered stale for map and dashboard use.
- If stale data exists, the system may return cached results immediately and refresh in the background.

### Background work

Use FastAPI `BackgroundTasks` for v1. No dedicated queue service is required.

Background work includes:

- external-risk refresh
- report generation
- import post-processing

### Failure behavior

- If the search provider is unavailable, use the latest cached results when available.
- If report generation fails, keep the report row with `failed` status and store the error message.
- If an agent fails during chat, return a partial answer with a visible limitation notice.

## Data Flow By Feature

### Dashboard flow

1. Read aggregated sqlite data.
2. Merge recent active external-risk events and country scores.
3. Compute KPI and alert payload.
4. Return `summary` and `alerts` API payloads.

### Chat flow

1. Persist user message to the current chat session.
2. Detect the question scope and required agents.
3. Call agent modules and collect citations.
4. Persist assistant message with trace metadata.
5. Return the assistant response payload.

### Map flow

1. Read current country scores and active risk events.
2. Return country summary list for map coloring.
3. On country click, return country detail with issues, suppliers, and products.

### Product detail flow

1. Load product metadata and current supplier links.
2. Load `3-5 years` of sales history aggregates and latest inventory status.
3. Load fulfillment summary and linked risk events.
4. Return a single consolidated product payload.

### Report generation flow

1. Receive scope request such as `dashboard`, `product`, or `country`.
2. Resolve the underlying data and agent calls.
3. Build a structured report object.
4. Save JSON and Markdown artifacts locally.
5. Persist report metadata and return status.

## Planned Code Organization

```text
frontend/
├── app/
├── components/
├── lib/
├── hooks/
└── types/

backend/
└── app/
    ├── api/
    ├── agents/
    ├── db/
    ├── services/
    ├── adapters/
    ├── reports/
    └── schemas/
```

## Cross-Cutting Rules

- All risk severity values must use the same numeric scale.
- All citation-bearing outputs must preserve source URL and title.
- The same backend data model must feed dashboard, map, product detail, reports, and chat.
- Every agent run should be traceable through sqlite metadata and local logs.
- V1 must run from the project directory without requiring cloud infrastructure.
