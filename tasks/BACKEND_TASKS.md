# BACKEND TASKS

Each task below is a complete backend step. A step should close one backend capability or one backend slice that leaves the system in a coherent state.

## BE-01 Project Structure And Config

### Goal

Create the FastAPI project skeleton and runtime configuration model.

### Deliverables

- Backend app package structure
- Environment and settings model
- Health endpoint baseline
- Provider adapter interfaces for LLM and search
- Local path configuration rules

### Dependencies

- None

### Acceptance criteria

- The backend boots with a documented local configuration.
- Storage paths and provider flags are accessible from configuration.
- The adapter boundaries exist before provider-specific code is added.

## BE-02 sqlite Schema And Data Access

### Goal

Create the sqlite schema and repository/data-access layer described in `DATA_MODEL.md`.

### Deliverables

- Schema creation and bootstrap logic
- Table definitions for all documented entities
- Data-access utilities or repositories
- Seed-safe initialization flow

### Dependencies

- `BE-01`

### Acceptance criteria

- The local database can be created from scratch.
- All documented tables exist and are queryable.
- Backend modules can read and write the required entities without raw SQL duplication everywhere.

## BE-03 Local File Storage Layout

### Goal

Create the project-managed filesystem structure for imports, reports, cache, and logs.

### Deliverables

- Directory bootstrap logic
- Path helpers for reports, imports, cache, and logs
- File-writing utilities for JSON and Markdown artifacts
- Consistent naming strategy for generated files

### Dependencies

- `BE-01`

### Acceptance criteria

- All documented data directories can be created locally.
- Report and cache writers resolve project-managed paths only.
- No source directory is used for runtime-generated artifacts.

## BE-04 Import Pipeline And Seed Data

### Goal

Implement CSV ingestion for products, suppliers, sales, and inventory data, plus a development seed strategy.

### Deliverables

- Import service for each required import type
- Raw file persistence in `data/imports/raw/`
- Import run tracking in sqlite
- Normalization and validation rules
- Seed dataset plan for local development

### Dependencies

- `BE-02`
- `BE-03`

### Acceptance criteria

- A valid CSV import creates an `imports` record and persists normalized data.
- Failed imports return row-count and error summaries.
- The backend can be populated locally without external services.

## BE-05 External Risk Agent

### Goal

Implement the search-backed agent that monitors geopolitical, tariff, logistics, weather, and labor disruptions.

### Deliverables

- External risk service and adapter integration
- Citation normalization
- Risk-event persistence
- Country score aggregation
- Cached result handling and stale-data policy

### Dependencies

- `BE-01`
- `BE-02`
- `BE-03`

### Acceptance criteria

- The agent can produce country-level scores and issue lists.
- Citation metadata is preserved in stored outputs.
- Cached results are used when live search is unavailable.

## BE-06 Demand Agent

### Goal

Implement demand analysis using `3-5 years` of sales history.

### Deliverables

- Sales aggregation logic
- Seasonality and spike detection
- Demand risk scoring
- Forecast window output suitable for product and dashboard views

### Dependencies

- `BE-02`
- `BE-04`

### Acceptance criteria

- The agent can score a product or product set using historical sales data.
- Sparse-history cases return a low-confidence or limited result rather than failing.
- Output shape matches `AGENTS.md` and `API_SPEC.md`.

## BE-07 Inventory Agent

### Goal

Implement inventory health analysis and reorder risk scoring.

### Deliverables

- Inventory snapshot queries
- Stockout and days-of-cover logic
- Reorder urgency logic
- Recommended-action generation

### Dependencies

- `BE-02`
- `BE-04`
- `BE-06`

### Acceptance criteria

- The agent returns a deterministic stock health summary for a product or product set.
- Inventory outputs can be combined with demand outputs for product and dashboard use.
- Missing inbound data produces a partial but usable result.

## BE-08 Fulfillment Agent

### Goal

Implement fulfillment risk analysis using backlog, delay, and on-time metrics.

### Deliverables

- Fulfillment snapshot model and query layer
- Regional fulfillment status computation
- SLA risk scoring
- Optional enrichment with external-risk context

### Dependencies

- `BE-02`
- `BE-04`
- `BE-05`

### Acceptance criteria

- The agent returns regional fulfillment summaries and a fulfillment risk score.
- Missing fulfillment data yields a partial response with clear limitations.
- Output can feed dashboard, product detail, chat, and reports.

## BE-09 Reporting Agent

### Goal

Implement local report generation for JSON and Markdown artifacts.

### Deliverables

- Report generation service
- JSON serializer
- Markdown renderer
- Report metadata persistence
- Failure handling for partial or failed generations

### Dependencies

- `BE-03`
- `BE-05`
- `BE-06`
- `BE-07`
- `BE-08`

### Acceptance criteria

- A report request creates a `reports` row and local artifacts.
- Completed reports store both JSON and Markdown paths.
- Failed reports preserve status and error details.

## BE-10 Chat Orchestration

### Goal

Implement session persistence and question routing across the domain agents.

### Deliverables

- Chat session service
- Message persistence
- Intent-to-agent routing
- Assistant response assembly
- Citation and used-agent metadata support

### Dependencies

- `BE-02`
- `BE-05`
- `BE-06`
- `BE-07`
- `BE-08`

### Acceptance criteria

- A user message can be persisted and answered through the orchestrator.
- Session history is queryable and reusable.
- Partial agent failures do not collapse the entire chat response.

## BE-11 Dashboard, Map, And Product APIs

### Goal

Implement the read APIs for dashboard summary, alerts, map data, product search, and product detail.

### Deliverables

- `GET /api/dashboard/summary`
- `GET /api/dashboard/alerts`
- `GET /api/map/countries`
- `GET /api/map/countries/{country_code}`
- `GET /api/products`
- `GET /api/products/{product_id}`

### Dependencies

- `BE-05`
- `BE-06`
- `BE-07`
- `BE-08`

### Acceptance criteria

- API payloads align with `API_SPEC.md`.
- Frontend pages can render against these endpoints without extra backend calls.
- Errors use the shared error response pattern.

## BE-12 Chat, Reports, And Imports APIs

### Goal

Implement the write and read APIs for chat sessions, chat messages, reports, health, and imports.

### Deliverables

- `GET /api/health`
- `GET /api/chat/sessions`
- `POST /api/chat/sessions`
- `GET /api/chat/sessions/{session_id}/messages`
- `POST /api/chat/messages`
- `GET /api/reports`
- `GET /api/reports/{report_id}`
- `POST /api/reports/generate`
- `GET /api/imports`
- `POST /api/imports/products`
- `POST /api/imports/sales`
- `POST /api/imports/inventory`
- `POST /api/imports/suppliers`

### Dependencies

- `BE-04`
- `BE-09`
- `BE-10`

### Acceptance criteria

- All listed endpoints are implemented and documented.
- Request and response shapes match `API_SPEC.md`.
- Long-running actions return usable status states.

## BE-13 Caching And Background Refresh

### Goal

Implement lightweight background work and cache handling for external risk and report generation.

### Deliverables

- External-risk cache reader and writer
- Stale-data policy using the documented freshness window
- Background task hooks for refresh and report generation
- Freshness metadata for downstream APIs

### Dependencies

- `BE-05`
- `BE-09`
- `BE-12`

### Acceptance criteria

- Cached external-risk data can be served when live search is unavailable.
- Background refresh does not break page response contracts.
- Freshness timestamps are visible in relevant API responses.

## BE-14 Tests And Eval Scenarios

### Goal

Add verification coverage for data flow, page contracts, and key product scenarios.

### Deliverables

- Schema and import tests
- Agent output tests
- API contract tests
- Scenario tests for map, dashboard, chat, product detail, and report generation
- Regression checklist tied to the docs

### Dependencies

- `BE-11`
- `BE-12`
- `BE-13`

### Acceptance criteria

- The documented product scenarios are testable and covered.
- Backend changes can be checked against stable expectations.
- The test set verifies cross-surface consistency for shared entities and risk outputs.
