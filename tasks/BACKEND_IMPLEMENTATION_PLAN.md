# BACKEND IMPLEMENTATION PLAN

This file is the execution-oriented backend tracker for ChainWatch.

It is a companion to:

- `tasks/STATUS.md` for official task state
- `tasks/BACKEND_TASKS.md` for task definitions and acceptance criteria
- `tasks/DECISIONS.md` for implementation decisions
- `tasks/ISSUES.md` for blockers and follow-ups

`tasks/STATUS.md` remains the source of truth for `Todo`, `In Progress`, `Blocked`, and `Done`.

## Purpose

Use this file to:

- group backend work into delivery phases
- track what is implemented and what is still missing
- break tasks into concrete checkpoints
- capture evidence and notes as implementation progresses

## Current Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Backend codebase | Implemented | FastAPI backend foundation now exists under `backend/` |
| Database schema | Implemented | sqlite bootstrap and repositories are live in phase 1 |
| File storage layout | Implemented | Managed runtime paths are created under `data/` at startup |
| Import pipeline | Implemented | CSV import services, import-run tracking, and seed tooling are now in place |
| Agents | Implemented for phase 4 | External risk, demand, inventory, fulfillment, reporting, and chat orchestration are now wired with trace metadata |
| REST API | Implemented through phase 6 | Dashboard, map, products, chat, reports, imports, and health endpoints now expose freshness metadata and background hooks where relevant |
| Tests | Implemented for phases 1-6 | `pytest` now covers bootstrap, storage, schema, health, imports, seed, agents, reports, chat orchestration, API endpoints, and cross-surface scenarios |

## Working Rules

1. Move task state in `tasks/STATUS.md` before or alongside major implementation work.
2. Update this file with checklist progress and implementation notes.
3. Record durable tradeoffs in `tasks/DECISIONS.md`.
4. Record blockers and unresolved follow-ups in `tasks/ISSUES.md`.

## Phase 1: Backend Foundation

This phase sets up the local runtime, persistence layer, and filesystem structure.

### BE-01 Project Structure And Config

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | High |
| Depends on | None |
| Goal | Create the FastAPI project skeleton and runtime configuration model |

Implementation checkpoints:

- [x] Create `backend/` project root
- [x] Create FastAPI app entrypoint
- [x] Create application package structure under `backend/app/`
- [x] Add configuration and settings model
- [x] Add local path configuration for database, cache, imports, reports, and logs
- [x] Add provider configuration flags for LLM and search adapters
- [x] Define provider adapter interfaces
- [x] Implement baseline `GET /api/health`
- [x] Document local backend startup flow

Definition of done:

- [x] Backend boots locally
- [x] Config values are available through a typed settings model
- [x] Health endpoint returns runtime readiness and provider flags
- [x] Adapter boundaries exist without provider-specific logic leaking into services

Notes:

- Current repo state is documentation-only, so this task starts from zero.
- Keep the backend minimal and explicit. Avoid introducing a heavy agent framework.

Evidence:

- `backend/pyproject.toml` defines the isolated backend project and dependencies
- `backend/app/main.py` boots the FastAPI app and runtime bootstrap flow
- `backend/app/config.py` provides the typed settings model and provider flags
- `backend/README.md` documents setup, run, and test commands

### BE-02 sqlite Schema And Data Access

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | High |
| Depends on | `BE-01` |
| Goal | Create the sqlite schema and data-access layer described in `DATA_MODEL.md` |

Implementation checkpoints:

- [x] Create sqlite bootstrap flow
- [x] Create schema file or equivalent bootstrap definitions
- [x] Create all documented tables
- [x] Add indexes required for common read paths
- [x] Add connection helper and transaction handling
- [x] Add repository or data-access layer for shared queries
- [x] Avoid duplicated raw SQL across modules
- [x] Ensure schema creation is safe to run on a new local setup

Core tables to implement:

- [x] `products`
- [x] `suppliers`
- [x] `product_suppliers`
- [x] `sales_history`
- [x] `inventory_snapshots`
- [x] `fulfillment_snapshots`
- [x] `risk_events`
- [x] `country_risk_scores`
- [x] `reports`
- [x] `chat_sessions`
- [x] `chat_messages`
- [x] `imports`
- [x] `agent_runs`

Definition of done:

- [x] Local database can be created from scratch
- [x] All documented tables are queryable
- [x] Shared repository helpers exist for read and write flows
- [x] Backend modules can use the data layer without scattering schema knowledge everywhere

Notes:

- Prefer explicit `sqlite3` access with a thin repository layer.
- The schema must support dashboard, map, product detail, chat, reports, and import flows from the beginning.

Evidence:

- `backend/app/db/schema.sql` contains the full phase-1 schema and indexes
- `backend/app/db/bootstrap.py` applies the schema idempotently at startup
- `backend/app/db/connection.py` enables sqlite row access, transactions, and foreign keys
- `backend/app/db/repositories/` provides shared repository helpers plus system and catalog smoke-path repositories

### BE-03 Local File Storage Layout

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | High |
| Depends on | `BE-01` |
| Goal | Create the project-managed filesystem structure for imports, reports, cache, and logs |

Implementation checkpoints:

- [x] Create directory bootstrap logic
- [x] Create path helpers for all managed storage locations
- [x] Create JSON artifact writer
- [x] Create Markdown artifact writer
- [x] Create cache read and write helpers
- [x] Create log path helpers
- [x] Define stable file naming strategy for reports and cache entries
- [x] Prevent writes outside project-managed runtime directories

Managed paths to support:

- [x] `data/app.db`
- [x] `data/imports/raw/`
- [x] `data/imports/processed/`
- [x] `data/reports/json/`
- [x] `data/reports/markdown/`
- [x] `data/cache/external_risk/`
- [x] `data/logs/app/`
- [x] `data/logs/agent_runs/`

Definition of done:

- [x] All required runtime directories can be created locally
- [x] Report writers resolve only project-managed paths
- [x] Cache and log helpers are reusable by agents and services
- [x] No runtime-generated artifacts are written into source directories

Notes:

- This task should land before report generation or external-risk caching work begins.

Evidence:

- `backend/app/services/storage.py` manages safe runtime path resolution and artifact writers
- Runtime bootstrap provisions the managed `data/` layout automatically before serving requests
- `backend/tests/test_storage.py` verifies safe path resolution and cache helpers

## Phase 2: Data Readiness

### BE-04 Import Pipeline And Seed Data

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | High |
| Depends on | `BE-02`, `BE-03` |
| Goal | Implement CSV ingestion and local seed data for products, suppliers, sales, inventory, and fulfillment |

Implementation checkpoints:

- [x] Define CSV formats for each import type
- [x] Persist raw files in `data/imports/raw/`
- [x] Track import runs in sqlite
- [x] Normalize and validate rows
- [x] Write normalized data into sqlite tables
- [x] Add seed dataset strategy for local development
- [x] Return row counts and error summaries for failures

Definition of done:

- [x] Valid imports create `imports` records
- [x] Normalized data is queryable through the backend
- [x] Failed imports return useful diagnostics
- [x] A local developer can populate the app without external services

Evidence:

- `backend/app/services/imports/service.py` implements transactional CSV import services for suppliers, products, sales, inventory, and fulfillment
- `backend/app/db/repositories/import_repository.py` tracks import runs in sqlite
- `backend/app/services/storage.py` persists raw import files and processed summary artifacts
- `backend/app/import_csv.py` provides a local CLI for manual CSV imports before the import APIs are added
- `backend/app/services/imports/seed.py` and `backend/app/seed.py` provide repeatable local demo data seeding
- `backend/tests/test_imports.py` and `backend/tests/test_seed.py` verify import success, validation failure, and seed population flows

## Phase 3: Core Analysis Agents

### BE-05 External Risk Agent

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | High |
| Depends on | `BE-01`, `BE-02`, `BE-03` |
| Goal | Implement search-backed external disruption analysis with citations and caching |

Implementation checkpoints:

- [x] Define structured input and output models
- [x] Implement `SearchAdapter` integration boundary
- [x] Implement citation normalization
- [x] Persist `risk_events`
- [x] Aggregate `country_risk_scores`
- [x] Implement cached result handling
- [x] Support stale-data fallback
- [x] Record `agent_runs` trace metadata

Definition of done:

- [x] Country-level scores and issue lists are produced
- [x] Citation metadata is preserved
- [x] Cache is used when live search is unavailable
- [x] Outputs align with `AGENTS.md`

Evidence:

- `backend/app/agents/external_risk.py` implements live-search normalization, sqlite persistence, and cache fallback behavior
- `backend/app/db/repositories/risk_repository.py` persists `risk_events` and `country_risk_scores`
- `backend/app/services/citations.py` normalizes and deduplicates citations
- `backend/tests/test_agents.py` verifies fresh-search output, sqlite persistence, and cached fallback behavior

### BE-06 Demand Agent

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | High |
| Depends on | `BE-02`, `BE-04` |
| Goal | Implement seasonality, spike detection, and demand risk scoring using `3-5 years` of sales history |

Implementation checkpoints:

- [x] Define structured input and output models
- [x] Implement sales aggregation logic
- [x] Implement seasonality detection
- [x] Implement recent spike detection
- [x] Implement forecast window output
- [x] Implement low-confidence behavior for sparse history
- [x] Record `agent_runs` trace metadata

Definition of done:

- [x] Product or product-set demand scoring is deterministic
- [x] Sparse-history cases return limited or low-confidence output
- [x] Output aligns with `AGENTS.md` and `API_SPEC.md`

Evidence:

- `backend/app/agents/demand.py` aggregates multi-year sales history into trend, seasonality, spike, forecast, and risk outputs
- `backend/app/db/repositories/analytics_repository.py` provides the sales query layer used by the demand workflow
- `backend/tests/test_agents.py` verifies both the seeded happy path and sparse-history low-confidence behavior

### BE-07 Inventory Agent

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | High |
| Depends on | `BE-02`, `BE-04`, `BE-06` |
| Goal | Implement stock health, reorder urgency, and stockout risk scoring |

Implementation checkpoints:

- [x] Define structured input and output models
- [x] Query latest inventory snapshots
- [x] Implement days-of-cover logic
- [x] Implement reorder urgency logic
- [x] Implement recommended-action generation
- [x] Support partial outputs when inbound data is missing
- [x] Support static-threshold fallback when demand data is unavailable
- [x] Record `agent_runs` trace metadata

Definition of done:

- [x] Product or product-set inventory health can be computed deterministically
- [x] Inventory outputs combine cleanly with demand outputs
- [x] Missing inbound data does not block usable output

Evidence:

- `backend/app/agents/inventory.py` computes stock health, cover, threshold-based risk, and recommended actions
- `backend/tests/test_agents.py` verifies inventory scoring with demand signals and latest snapshot data

### BE-08 Fulfillment Agent

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | Medium |
| Depends on | `BE-02`, `BE-04`, `BE-05` |
| Goal | Implement fulfillment risk analysis using backlog, delays, on-time rate, and optional external-risk enrichment |

Implementation checkpoints:

- [x] Define structured input and output models
- [x] Query fulfillment snapshots
- [x] Compute regional fulfillment status
- [x] Compute fulfillment risk score
- [x] Support optional enrichment from external-risk outputs
- [x] Support partial result behavior for missing fulfillment data
- [x] Record `agent_runs` trace metadata

Definition of done:

- [x] Regional fulfillment summaries are returned
- [x] A fulfillment risk score is produced
- [x] Missing local or external context yields partial but usable output

Evidence:

- `backend/app/agents/fulfillment.py` aggregates latest fulfillment snapshots into regional and overall SLA risk outputs
- `backend/tests/test_agents.py` verifies regional aggregation and fulfillment risk scoring on the demo dataset

## Phase 4: Output And Orchestration

### BE-09 Reporting Agent

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | Medium |
| Depends on | `BE-03`, `BE-05`, `BE-06`, `BE-07`, `BE-08` |
| Goal | Generate local JSON and Markdown report artifacts with persisted metadata |

Implementation checkpoints:

- [x] Define report input and output models
- [x] Create report generation service
- [x] Serialize report JSON
- [x] Render report Markdown
- [x] Persist `reports` metadata
- [x] Preserve partial and failed generation states
- [x] Include visible limitations when upstream data is incomplete

Definition of done:

- [x] Report requests create `reports` rows
- [x] Completed reports store JSON and Markdown paths
- [x] Partial or failed runs preserve status and error details

Evidence:

- `backend/app/schemas/reports.py` defines report request, artifact, status, and generation-result models
- `backend/app/db/repositories/report_repository.py` persists queued, running, completed, partial, and failed report metadata
- `backend/app/agents/reporting.py` generates report sections, JSON artifacts, Markdown artifacts, and visible limitations
- `backend/tests/test_output_orchestration.py` verifies completed report generation and JSON-preserving partial behavior when Markdown rendering fails

### BE-10 Chat Orchestration

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | Medium |
| Depends on | `BE-02`, `BE-05`, `BE-06`, `BE-07`, `BE-08` |
| Goal | Route user questions to agents, merge outputs, preserve citations, and return one coherent answer |

Implementation checkpoints:

- [x] Create chat session service
- [x] Persist user and assistant messages
- [x] Implement intent-to-agent routing
- [x] Merge structured agent outputs
- [x] Preserve citations and used-agent metadata
- [x] Add graceful partial-failure behavior
- [x] Support deterministic fallback when LLM is unavailable
- [x] Record orchestrator trace metadata

Definition of done:

- [x] A user message can be persisted and answered
- [x] Session history is queryable and reusable
- [x] One failing agent does not collapse the whole response

Evidence:

- `backend/app/schemas/chat.py` defines chat session, message, scope, and orchestrator contracts
- `backend/app/db/repositories/chat_repository.py` persists sessions and ordered chat messages with citations and agent-trace metadata
- `backend/app/agents/chat_orchestrator.py` routes messages to domain agents, preserves citations, and falls back to deterministic assembly when the LLM is unavailable
- `backend/tests/test_output_orchestration.py` verifies message persistence, session history reuse, and graceful partial-failure handling

## Phase 5: API Surface

### BE-11 Dashboard, Map, And Product APIs

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | High |
| Depends on | `BE-05`, `BE-06`, `BE-07`, `BE-08` |
| Goal | Implement the read APIs for dashboard, map, and product detail flows |

Endpoints:

- [x] `GET /api/dashboard/summary`
- [x] `GET /api/dashboard/alerts`
- [x] `GET /api/map/countries`
- [x] `GET /api/map/countries/{country_code}`
- [x] `GET /api/products`
- [x] `GET /api/products/{product_id}`

Definition of done:

- [x] Payloads align with `API_SPEC.md`
- [x] Frontend can render these surfaces without extra backend calls
- [x] Errors use the shared error response pattern

Evidence:

- `backend/app/api/routes/dashboard.py`, `map.py`, and `products.py` expose the documented phase-5 read endpoints
- `backend/app/services/dashboard.py`, `map.py`, and `products.py` assemble dashboard, map, and product payloads from the phase-3 agent layer
- `backend/tests/test_api_endpoints.py` verifies dashboard, map, and product endpoint behavior including not-found handling

### BE-12 Chat, Reports, And Imports APIs

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | High |
| Depends on | `BE-04`, `BE-09`, `BE-10` |
| Goal | Implement the remaining read and write APIs for health, chat, reports, and imports |

Endpoints:

- [x] `GET /api/health`
- [x] `GET /api/chat/sessions`
- [x] `POST /api/chat/sessions`
- [x] `GET /api/chat/sessions/{session_id}/messages`
- [x] `POST /api/chat/messages`
- [x] `GET /api/reports`
- [x] `GET /api/reports/{report_id}`
- [x] `POST /api/reports/generate`
- [x] `GET /api/imports`
- [x] `POST /api/imports/products`
- [x] `POST /api/imports/sales`
- [x] `POST /api/imports/inventory`
- [x] `POST /api/imports/suppliers`

Definition of done:

- [x] Request and response shapes align with `API_SPEC.md`
- [x] Long-running actions expose usable status values
- [x] Health endpoint reflects runtime and provider readiness

Evidence:

- `backend/app/api/routes/chat.py`, `reports.py`, and `imports.py` expose the documented phase-5 write and read endpoints on top of the phase-4 services
- `backend/app/api/dependencies.py` centralizes runtime, adapter, and service construction for route handlers
- `backend/tests/test_api_endpoints.py` verifies chat session/message flows, report generation/list/detail flows, and import listing/start flows

## Phase 6: Reliability

### BE-13 Caching And Background Refresh

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | Medium |
| Depends on | `BE-05`, `BE-09`, `BE-12` |
| Goal | Implement background refresh and cache behavior for external risk and reports |

Implementation checkpoints:

- [x] Implement external-risk cache reader and writer
- [x] Implement stale-data policy
- [x] Add background task hooks for refresh
- [x] Add background task hooks for report generation
- [x] Expose freshness metadata in relevant APIs

Definition of done:

- [x] Cached external-risk data can be served when live search fails
- [x] Background refresh preserves page contracts
- [x] Freshness timestamps are visible downstream

Evidence:

- `backend/app/services/external_risk.py` adds cache-aware page reads, stale-cache detection, and background refresh hooks for external-risk consumers
- `backend/app/api/routes/reports.py` queues report generation and starts background processing without changing the route contract
- Dashboard, map, product detail, and report detail payloads now include freshness metadata through their API schemas and services
- `backend/tests/test_api_endpoints.py` verifies stale-cache freshness signaling and queued report generation behavior

### BE-14 Tests And Eval Scenarios

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | Medium |
| Depends on | `BE-11`, `BE-12`, `BE-13` |
| Goal | Add verification coverage for schema, imports, agents, APIs, and end-to-end scenarios |

Implementation checkpoints:

- [x] Add schema bootstrap tests
- [x] Add import pipeline tests
- [x] Add agent output tests
- [x] Add API contract tests
- [x] Add scenario tests for dashboard, map, chat, product detail, and reports
- [x] Add regression checklist tied to docs

Definition of done:

- [x] Core product scenarios are testable and covered
- [x] Shared entity consistency is verified across surfaces
- [x] Regressions can be checked against stable expectations

Evidence:

- Existing test modules continue to cover schema bootstrap, imports, agents, and API contracts
- `backend/tests/test_scenarios.py` adds cross-surface scenario coverage for dashboard, map, chat, product detail, and reports
- `tasks/REGRESSION_CHECKLIST.md` ties the regression pass back to the documented API and surface contracts

## Suggested First Execution Sequence

1. Add `BE-11` product and dashboard APIs
2. Finish reporting, chat, and reliability work
