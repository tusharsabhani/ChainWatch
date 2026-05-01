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
| Import pipeline | Not started | No CSV ingestion code yet |
| Agents | Not started | Agent behavior is documented in `AGENTS.md` only |
| REST API | Started | `GET /api/health` is implemented; feature APIs remain pending |
| Tests | Implemented for phase 1 | `pytest` covers bootstrap, storage, schema, health, and repository smoke paths |

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
| Status | Not started |
| Priority | High |
| Depends on | `BE-02`, `BE-03` |
| Goal | Implement CSV ingestion and local seed data for products, suppliers, sales, inventory, and fulfillment |

Implementation checkpoints:

- [ ] Define CSV formats for each import type
- [ ] Persist raw files in `data/imports/raw/`
- [ ] Track import runs in sqlite
- [ ] Normalize and validate rows
- [ ] Write normalized data into sqlite tables
- [ ] Add seed dataset strategy for local development
- [ ] Return row counts and error summaries for failures

Definition of done:

- [ ] Valid imports create `imports` records
- [ ] Normalized data is queryable through the backend
- [ ] Failed imports return useful diagnostics
- [ ] A local developer can populate the app without external services

Evidence:

- None yet

## Phase 3: Core Analysis Agents

### BE-05 External Risk Agent

| Field | Value |
| --- | --- |
| Status | Not started |
| Priority | High |
| Depends on | `BE-01`, `BE-02`, `BE-03` |
| Goal | Implement search-backed external disruption analysis with citations and caching |

Implementation checkpoints:

- [ ] Define structured input and output models
- [ ] Implement `SearchAdapter` integration boundary
- [ ] Implement citation normalization
- [ ] Persist `risk_events`
- [ ] Aggregate `country_risk_scores`
- [ ] Implement cached result handling
- [ ] Support stale-data fallback
- [ ] Record `agent_runs` trace metadata

Definition of done:

- [ ] Country-level scores and issue lists are produced
- [ ] Citation metadata is preserved
- [ ] Cache is used when live search is unavailable
- [ ] Outputs align with `AGENTS.md`

Evidence:

- None yet

### BE-06 Demand Agent

| Field | Value |
| --- | --- |
| Status | Not started |
| Priority | High |
| Depends on | `BE-02`, `BE-04` |
| Goal | Implement seasonality, spike detection, and demand risk scoring using `3-5 years` of sales history |

Implementation checkpoints:

- [ ] Define structured input and output models
- [ ] Implement sales aggregation logic
- [ ] Implement seasonality detection
- [ ] Implement recent spike detection
- [ ] Implement forecast window output
- [ ] Implement low-confidence behavior for sparse history
- [ ] Record `agent_runs` trace metadata

Definition of done:

- [ ] Product or product-set demand scoring is deterministic
- [ ] Sparse-history cases return limited or low-confidence output
- [ ] Output aligns with `AGENTS.md` and `API_SPEC.md`

Evidence:

- None yet

### BE-07 Inventory Agent

| Field | Value |
| --- | --- |
| Status | Not started |
| Priority | High |
| Depends on | `BE-02`, `BE-04`, `BE-06` |
| Goal | Implement stock health, reorder urgency, and stockout risk scoring |

Implementation checkpoints:

- [ ] Define structured input and output models
- [ ] Query latest inventory snapshots
- [ ] Implement days-of-cover logic
- [ ] Implement reorder urgency logic
- [ ] Implement recommended-action generation
- [ ] Support partial outputs when inbound data is missing
- [ ] Support static-threshold fallback when demand data is unavailable
- [ ] Record `agent_runs` trace metadata

Definition of done:

- [ ] Product or product-set inventory health can be computed deterministically
- [ ] Inventory outputs combine cleanly with demand outputs
- [ ] Missing inbound data does not block usable output

Evidence:

- None yet

### BE-08 Fulfillment Agent

| Field | Value |
| --- | --- |
| Status | Not started |
| Priority | Medium |
| Depends on | `BE-02`, `BE-04`, `BE-05` |
| Goal | Implement fulfillment risk analysis using backlog, delays, on-time rate, and optional external-risk enrichment |

Implementation checkpoints:

- [ ] Define structured input and output models
- [ ] Query fulfillment snapshots
- [ ] Compute regional fulfillment status
- [ ] Compute fulfillment risk score
- [ ] Support optional enrichment from external-risk outputs
- [ ] Support partial result behavior for missing fulfillment data
- [ ] Record `agent_runs` trace metadata

Definition of done:

- [ ] Regional fulfillment summaries are returned
- [ ] A fulfillment risk score is produced
- [ ] Missing local or external context yields partial but usable output

Evidence:

- None yet

## Phase 4: Output And Orchestration

### BE-09 Reporting Agent

| Field | Value |
| --- | --- |
| Status | Not started |
| Priority | Medium |
| Depends on | `BE-03`, `BE-05`, `BE-06`, `BE-07`, `BE-08` |
| Goal | Generate local JSON and Markdown report artifacts with persisted metadata |

Implementation checkpoints:

- [ ] Define report input and output models
- [ ] Create report generation service
- [ ] Serialize report JSON
- [ ] Render report Markdown
- [ ] Persist `reports` metadata
- [ ] Preserve partial and failed generation states
- [ ] Include visible limitations when upstream data is incomplete

Definition of done:

- [ ] Report requests create `reports` rows
- [ ] Completed reports store JSON and Markdown paths
- [ ] Partial or failed runs preserve status and error details

Evidence:

- None yet

### BE-10 Chat Orchestration

| Field | Value |
| --- | --- |
| Status | Not started |
| Priority | Medium |
| Depends on | `BE-02`, `BE-05`, `BE-06`, `BE-07`, `BE-08` |
| Goal | Route user questions to agents, merge outputs, preserve citations, and return one coherent answer |

Implementation checkpoints:

- [ ] Create chat session service
- [ ] Persist user and assistant messages
- [ ] Implement intent-to-agent routing
- [ ] Merge structured agent outputs
- [ ] Preserve citations and used-agent metadata
- [ ] Add graceful partial-failure behavior
- [ ] Support deterministic fallback when LLM is unavailable
- [ ] Record orchestrator trace metadata

Definition of done:

- [ ] A user message can be persisted and answered
- [ ] Session history is queryable and reusable
- [ ] One failing agent does not collapse the whole response

Evidence:

- None yet

## Phase 5: API Surface

### BE-11 Dashboard, Map, And Product APIs

| Field | Value |
| --- | --- |
| Status | Not started |
| Priority | High |
| Depends on | `BE-05`, `BE-06`, `BE-07`, `BE-08` |
| Goal | Implement the read APIs for dashboard, map, and product detail flows |

Endpoints:

- [ ] `GET /api/dashboard/summary`
- [ ] `GET /api/dashboard/alerts`
- [ ] `GET /api/map/countries`
- [ ] `GET /api/map/countries/{country_code}`
- [ ] `GET /api/products`
- [ ] `GET /api/products/{product_id}`

Definition of done:

- [ ] Payloads align with `API_SPEC.md`
- [ ] Frontend can render these surfaces without extra backend calls
- [ ] Errors use the shared error response pattern

Evidence:

- None yet

### BE-12 Chat, Reports, And Imports APIs

| Field | Value |
| --- | --- |
| Status | Not started |
| Priority | High |
| Depends on | `BE-04`, `BE-09`, `BE-10` |
| Goal | Implement the remaining read and write APIs for health, chat, reports, and imports |

Endpoints:

- [ ] `GET /api/health`
- [ ] `GET /api/chat/sessions`
- [ ] `POST /api/chat/sessions`
- [ ] `GET /api/chat/sessions/{session_id}/messages`
- [ ] `POST /api/chat/messages`
- [ ] `GET /api/reports`
- [ ] `GET /api/reports/{report_id}`
- [ ] `POST /api/reports/generate`
- [ ] `GET /api/imports`
- [ ] `POST /api/imports/products`
- [ ] `POST /api/imports/sales`
- [ ] `POST /api/imports/inventory`
- [ ] `POST /api/imports/suppliers`

Definition of done:

- [ ] Request and response shapes align with `API_SPEC.md`
- [ ] Long-running actions expose usable status values
- [ ] Health endpoint reflects runtime and provider readiness

Evidence:

- None yet

## Phase 6: Reliability

### BE-13 Caching And Background Refresh

| Field | Value |
| --- | --- |
| Status | Not started |
| Priority | Medium |
| Depends on | `BE-05`, `BE-09`, `BE-12` |
| Goal | Implement background refresh and cache behavior for external risk and reports |

Implementation checkpoints:

- [ ] Implement external-risk cache reader and writer
- [ ] Implement stale-data policy
- [ ] Add background task hooks for refresh
- [ ] Add background task hooks for report generation
- [ ] Expose freshness metadata in relevant APIs

Definition of done:

- [ ] Cached external-risk data can be served when live search fails
- [ ] Background refresh preserves page contracts
- [ ] Freshness timestamps are visible downstream

Evidence:

- None yet

### BE-14 Tests And Eval Scenarios

| Field | Value |
| --- | --- |
| Status | Not started |
| Priority | Medium |
| Depends on | `BE-11`, `BE-12`, `BE-13` |
| Goal | Add verification coverage for schema, imports, agents, APIs, and end-to-end scenarios |

Implementation checkpoints:

- [ ] Add schema bootstrap tests
- [ ] Add import pipeline tests
- [ ] Add agent output tests
- [ ] Add API contract tests
- [ ] Add scenario tests for dashboard, map, chat, product detail, and reports
- [ ] Add regression checklist tied to docs

Definition of done:

- [ ] Core product scenarios are testable and covered
- [ ] Shared entity consistency is verified across surfaces
- [ ] Regressions can be checked against stable expectations

Evidence:

- None yet

## Suggested First Execution Sequence

1. Start `BE-04`
2. Build `BE-06` and `BE-07` first for the earliest useful product slice
3. Add `BE-05` and `BE-08`
4. Add `BE-11` product and dashboard APIs
5. Finish reporting, chat, and reliability work
