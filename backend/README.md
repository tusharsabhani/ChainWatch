# ChainWatch Backend

The backend is an isolated FastAPI project for the ChainWatch local-first runtime.

## Requirements

- `uv`
- Python `3.12`

## Setup

From the repository root:

```bash
cd backend
uv sync --extra dev
```

Optional provider configuration:

```bash
cp .env.example .env
```

Then configure any providers you want in `backend/.env`.

- Set `CHAINWATCH_LLM_PROVIDER=openai` to enable semantic chat routing and LLM-based answer composition.
- If `OPENAI_API_KEY` is present, ChainWatch uses the live OpenAI Responses API.
- If `CHAINWATCH_LLM_PROVIDER=openai` is set but no API key is present, ChainWatch falls back to a local mock OpenAI mode that still exercises tool routing and answer composition from the demo/mock data and structured agent outputs.
- Set `EXA_API_KEY` to enable live external-risk search. External-risk responses are reused from local cache for the same UTC day before another live search is attempted.
- If no search provider is configured, the app still runs, but external-risk sections may return cached results or an empty result with limitations.

## Run

From the `backend/` directory:

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## First Endpoint

- `GET /api/health`

This endpoint verifies runtime readiness, sqlite connectivity, managed storage paths, and provider configuration flags.

## Phase 5 APIs

Available endpoint groups:

- `GET /api/health`
- `GET /api/dashboard/summary`
- `GET /api/dashboard/alerts`
- `GET /api/map/countries`
- `GET /api/map/countries/{country_code}`
- `GET /api/products`
- `GET /api/products/{product_id}`
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

Reliability additions from phase 6:

- dashboard, map, product detail, and report detail responses include freshness metadata
- stale cached external-risk data can be served while a background refresh is scheduled
- report generation is queued first and then completed in a background task
- chat orchestration supports semantic routing through the shared LLM adapter with deterministic fallback when live LLM access is unavailable

## Import CSV Data

From the `backend/` directory:

```bash
uv run python -m app.import_csv suppliers /absolute/path/to/suppliers.csv
uv run python -m app.import_csv products /absolute/path/to/products.csv
uv run python -m app.import_csv sales /absolute/path/to/sales.csv
uv run python -m app.import_csv inventory /absolute/path/to/inventory.csv
uv run python -m app.import_csv fulfillment /absolute/path/to/fulfillment.csv
```

CSV formats:

- `suppliers`: `supplier_code`, `name`, `country_code`, `region`, `lead_time_days`, `reliability_score`, `active`
- `products`: `sku`, `name`, `category`, `brand`, `status`, `origin_country_code`, `default_supplier_code`, `alternate_supplier_codes`
- `sales`: `product_sku`, `sales_date`, `channel`, `region_code`, `units_sold`, `gross_revenue`, `net_revenue`, `returns_qty`, `promo_flag`, `stockout_flag`
- `inventory`: `product_sku`, `warehouse_code`, `snapshot_date`, `on_hand_qty`, `reserved_qty`, `inbound_qty`, `reorder_point`, `safety_stock`, `days_of_cover`
- `fulfillment`: `product_sku`, `region_code`, `warehouse_code`, `captured_at`, `backlog_orders`, `avg_ship_delay_hours`, `on_time_rate`, `sla_risk_level`

Each import creates:

- an `imports` row in sqlite
- a raw-file copy in `data/imports/raw/`
- a processed summary artifact in `data/imports/processed/`

Imports are transactional. If a CSV has validation errors, no normalized rows from that file are written.

Phase 5 import APIs accept a local file reference in JSON for v1:

```bash
curl -X POST http://127.0.0.1:8000/api/imports/suppliers \
  -H 'Content-Type: application/json' \
  -d '{"filePath":"/absolute/path/to/suppliers.csv"}'
```

## Seed Demo Data

From the `backend/` directory:

```bash
uv run python -m app.seed
```

This generates a local demo dataset and imports it through the same CSV pipeline used for manual imports.

What this includes:

- products
- suppliers
- sales history
- inventory snapshots
- fulfillment snapshots

What this does not include by itself:

- live external-risk events

For a fuller external-risk demo, configure `EXA_API_KEY` and then use the dashboard, map, chat, or product pages to trigger live searches. Without a search provider, those surfaces can still render but may show cached or empty external-risk results.

## External Risk Search

If `EXA_API_KEY` is configured, the backend uses Exa for external-risk searches through the shared `SearchAdapter` interface. Results are cached in `data/cache/external_risk/` and reused for the same UTC day before another live search is attempted.

## Core Agents

Phase 3 backend agents are implemented for:

- external risk
- demand
- inventory
- fulfillment

These agents run as Python services, create `agent_runs` trace rows plus local run logs, and currently power the page, chat, and reporting APIs.

## Reporting And Chat Services

Phase 4 backend services are implemented for:

- report generation
- chat orchestration

Current capabilities:

- `ReportService` creates `reports` rows, writes JSON and Markdown artifacts, and preserves partial or failed generation states
- `ChatService` creates chat sessions, persists user and assistant messages, and routes questions through the domain agents with citation preservation
- `Chat Orchestrator` uses the shared LLM adapter for semantic tool selection and final answer composition, with deterministic fallback when the live LLM path is unavailable
- `OpenAILLMAdapter` supports both live mode and a no-key mock mode for local-first development and evaluation

These flows are available through both Python services and the current HTTP API.

## Chat Routing Evals

The semantic routing eval cases live in `app/evals/chat_routing.py` and are covered by the backend test suite.

From the `backend/` directory:

```bash
uv run pytest tests/test_chat_routing_evals.py tests/test_llm_adapters.py
```

## Test

From the `backend/` directory:

```bash
uv run pytest
```

The cross-surface regression pass is documented in `tasks/REGRESSION_CHECKLIST.md`.
