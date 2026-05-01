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

## Run

From the `backend/` directory:

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## First Endpoint

- `GET /api/health`

This endpoint verifies runtime readiness, sqlite connectivity, managed storage paths, and provider configuration flags.

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

## Seed Demo Data

From the `backend/` directory:

```bash
uv run python -m app.seed
```

This generates a local demo dataset and imports it through the same CSV pipeline used for manual imports.

## Core Agents

Phase 3 backend agents are implemented for:

- external risk
- demand
- inventory
- fulfillment

These agents currently run as Python services and create `agent_runs` trace rows plus local run logs. Their page and chat APIs will be added in later backend phases.

## Test

From the `backend/` directory:

```bash
uv run pytest
```
