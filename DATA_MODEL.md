# DATA MODEL

This document defines the sqlite schema for ChainWatch. The schema is optimized for a local-first MVP and aims to support all v1 pages and agents without requiring external infrastructure.

## Conventions

- Use plural table names.
- Store timestamps as ISO 8601 strings in UTC.
- Store booleans as `INTEGER` values `0` or `1`.
- Use `INTEGER PRIMARY KEY` for local numeric entities and `TEXT` IDs for generated run/report/message entities.
- Keep raw provider payloads in JSON text fields only when they are needed for traceability.

## Relationship Overview

```text
products ---< sales_history
products ---< inventory_snapshots
products ---< fulfillment_snapshots
products ---< product_suppliers >--- suppliers
products ---< risk_events
suppliers ---< risk_events
country_risk_scores ---< risk_events
chat_sessions ---< chat_messages
reports ---< agent_runs (by trigger_ref when applicable)
imports tracks all CSV ingestion activity
```

## products

Purpose: master product catalog used across dashboard, product detail, reports, and chat.

| Column | Type | Notes |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY | Local product ID |
| sku | TEXT UNIQUE NOT NULL | External SKU identifier |
| name | TEXT NOT NULL | Product name |
| category | TEXT NOT NULL | Product category |
| brand | TEXT | Brand name |
| status | TEXT NOT NULL | `active`, `inactive`, `discontinued` |
| default_supplier_id | INTEGER | Optional FK to suppliers.id |
| origin_country_code | TEXT | ISO country code |
| created_at | TEXT NOT NULL | Audit field |
| updated_at | TEXT NOT NULL | Audit field |

Used by:

- Dashboard
- Product Detail
- Reports
- Chat
- Demand Agent
- Inventory Agent
- Fulfillment Agent

## suppliers

Purpose: supplier master data and country exposure source.

| Column | Type | Notes |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY | Local supplier ID |
| supplier_code | TEXT UNIQUE NOT NULL | External supplier identifier |
| name | TEXT NOT NULL | Supplier name |
| country_code | TEXT NOT NULL | ISO country code |
| region | TEXT | Broad region label |
| lead_time_days | INTEGER | Nominal lead time |
| reliability_score | REAL | Internal score from 0 to 100 |
| active | INTEGER NOT NULL | `1` active, `0` inactive |
| created_at | TEXT NOT NULL | Audit field |
| updated_at | TEXT NOT NULL | Audit field |

Used by:

- Dashboard
- Map
- Product Detail
- Reports
- External Risk Agent

## product_suppliers

Purpose: many-to-many mapping between products and suppliers.

| Column | Type | Notes |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY | Local mapping ID |
| product_id | INTEGER NOT NULL | FK to products.id |
| supplier_id | INTEGER NOT NULL | FK to suppliers.id |
| is_primary | INTEGER NOT NULL | `1` primary supplier |
| supplier_sku | TEXT | Supplier-facing SKU if available |
| lead_time_days | INTEGER | Override lead time for this product-supplier pair |
| min_order_qty | INTEGER | Optional MOQ |
| created_at | TEXT NOT NULL | Audit field |
| updated_at | TEXT NOT NULL | Audit field |

Used by:

- Product Detail
- Dashboard supplier exposure summaries
- Map country detail
- External Risk Agent

## sales_history

Purpose: historical sales series used by the Demand Agent. This table should support `3-5 years` of data.

| Column | Type | Notes |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY | Local sales record ID |
| product_id | INTEGER NOT NULL | FK to products.id |
| sales_date | TEXT NOT NULL | Daily or weekly bucket date |
| channel | TEXT NOT NULL | `web`, `marketplace`, `store`, or similar |
| region_code | TEXT NOT NULL | Internal region label |
| units_sold | INTEGER NOT NULL | Units sold in bucket |
| gross_revenue | REAL NOT NULL | Gross revenue |
| net_revenue | REAL NOT NULL | Net revenue |
| returns_qty | INTEGER NOT NULL | Returned units |
| promo_flag | INTEGER NOT NULL | Promotional activity present |
| stockout_flag | INTEGER NOT NULL | Product unavailable during bucket |

Used by:

- Demand Agent
- Dashboard trends
- Product Detail
- Reports

## inventory_snapshots

Purpose: current and historical stock position.

| Column | Type | Notes |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY | Local inventory snapshot ID |
| product_id | INTEGER NOT NULL | FK to products.id |
| warehouse_code | TEXT NOT NULL | Warehouse identifier |
| snapshot_date | TEXT NOT NULL | Snapshot timestamp |
| on_hand_qty | INTEGER NOT NULL | Current stock |
| reserved_qty | INTEGER NOT NULL | Reserved stock |
| inbound_qty | INTEGER NOT NULL | Pending inbound stock |
| reorder_point | INTEGER NOT NULL | Reorder threshold |
| safety_stock | INTEGER NOT NULL | Safety threshold |
| days_of_cover | REAL | Calculated inventory cover |

Used by:

- Inventory Agent
- Dashboard KPIs
- Product Detail
- Reports

## fulfillment_snapshots

Purpose: track regional fulfillment health.

| Column | Type | Notes |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY | Local fulfillment snapshot ID |
| product_id | INTEGER | Optional FK to products.id |
| region_code | TEXT NOT NULL | Delivery region |
| warehouse_code | TEXT | Related warehouse |
| captured_at | TEXT NOT NULL | Snapshot timestamp |
| backlog_orders | INTEGER NOT NULL | Pending orders |
| avg_ship_delay_hours | REAL NOT NULL | Average delay |
| on_time_rate | REAL NOT NULL | 0 to 1 ratio |
| sla_risk_level | INTEGER NOT NULL | Severity 1 to 5 |

Used by:

- Fulfillment Agent
- Dashboard trends
- Product Detail
- Reports

## risk_events

Purpose: store external or derived risk events that can affect products, suppliers, countries, or fulfillment outcomes.

| Column | Type | Notes |
| --- | --- | --- |
| id | TEXT PRIMARY KEY | Generated event ID |
| source_type | TEXT NOT NULL | `search`, `manual`, `derived` |
| risk_type | TEXT NOT NULL | `geopolitical`, `tariff`, `logistics`, `weather`, `labor`, `demand`, `inventory`, `fulfillment` |
| severity | INTEGER NOT NULL | Severity 1 to 5 |
| title | TEXT NOT NULL | Event title |
| summary | TEXT NOT NULL | Event summary |
| country_code | TEXT | ISO country code |
| route_code | TEXT | Optional route or lane identifier |
| affected_supplier_id | INTEGER | Optional FK to suppliers.id |
| affected_product_id | INTEGER | Optional FK to products.id |
| event_date | TEXT | Source event timestamp |
| detected_at | TEXT NOT NULL | Detection time |
| expires_at | TEXT | Optional expiry |
| status | TEXT NOT NULL | `open`, `monitoring`, `resolved` |
| source_url | TEXT | Citation URL |
| source_name | TEXT | Citation publisher |
| citation_snippet | TEXT | Short source excerpt |
| confidence | REAL | Confidence score 0 to 1 |
| payload_json | TEXT | Raw or normalized detail |

Used by:

- External Risk Agent
- Dashboard alerts
- Map
- Product Detail
- Reports
- Chat

## country_risk_scores

Purpose: store a normalized country-level view for map rendering and dashboard exposure summaries.

| Column | Type | Notes |
| --- | --- | --- |
| id | INTEGER PRIMARY KEY | Local score row ID |
| country_code | TEXT NOT NULL | ISO country code |
| score_date | TEXT NOT NULL | Snapshot date |
| overall_score | REAL NOT NULL | Aggregate risk score |
| geopolitical_score | REAL NOT NULL | Category score |
| tariff_score | REAL NOT NULL | Category score |
| logistics_score | REAL NOT NULL | Category score |
| weather_score | REAL NOT NULL | Category score |
| labor_score | REAL NOT NULL | Category score |
| active_event_count | INTEGER NOT NULL | Open events count |
| highest_severity | INTEGER NOT NULL | Severity 1 to 5 |
| summary | TEXT | Short country summary |

Used by:

- Map
- Dashboard
- Reports
- External Risk Agent

## reports

Purpose: metadata for generated reports and local artifact locations.

| Column | Type | Notes |
| --- | --- | --- |
| id | TEXT PRIMARY KEY | Generated report ID |
| report_type | TEXT NOT NULL | `risk_summary`, `product_risk`, `country_risk`, `supplier_risk`, `chat_export` |
| scope_type | TEXT NOT NULL | `dashboard`, `product`, `country`, `supplier`, `chat` |
| scope_id | TEXT | Related entity ID |
| title | TEXT NOT NULL | Report title |
| status | TEXT NOT NULL | `queued`, `running`, `completed`, `partial`, `failed` |
| requested_by | TEXT | Optional local actor |
| created_at | TEXT NOT NULL | Creation time |
| completed_at | TEXT | Completion time |
| json_path | TEXT | Path to JSON artifact |
| markdown_path | TEXT | Path to Markdown artifact |
| summary | TEXT | One-line description |
| error_message | TEXT | Failure reason if any |

Used by:

- Reports page
- Reporting Agent
- Product Detail quick actions
- Map quick actions

## chat_sessions

Purpose: top-level chat sessions.

| Column | Type | Notes |
| --- | --- | --- |
| id | TEXT PRIMARY KEY | Generated session ID |
| title | TEXT NOT NULL | Session title |
| context_scope | TEXT NOT NULL | `global`, `product`, `supplier`, `country` |
| context_id | TEXT | Optional entity ID |
| created_at | TEXT NOT NULL | Creation time |
| updated_at | TEXT NOT NULL | Last update time |
| last_message_at | TEXT NOT NULL | Used for sorting |

Used by:

- Chat page
- Chat Orchestrator

## chat_messages

Purpose: ordered messages within a session.

| Column | Type | Notes |
| --- | --- | --- |
| id | TEXT PRIMARY KEY | Generated message ID |
| session_id | TEXT NOT NULL | FK to chat_sessions.id |
| role | TEXT NOT NULL | `user`, `assistant`, `system` |
| message_text | TEXT NOT NULL | Raw message content |
| citations_json | TEXT | Serialized citations |
| agent_trace_json | TEXT | Agent summary metadata |
| created_at | TEXT NOT NULL | Message time |

Used by:

- Chat page
- Reports when exporting chat-linked reports

## imports

Purpose: track local CSV import activity and outcomes.

| Column | Type | Notes |
| --- | --- | --- |
| id | TEXT PRIMARY KEY | Generated import ID |
| import_type | TEXT NOT NULL | `products`, `suppliers`, `sales`, `inventory`, `fulfillment` |
| filename | TEXT NOT NULL | Original file name |
| status | TEXT NOT NULL | `queued`, `processing`, `completed`, `failed` |
| row_count | INTEGER NOT NULL | Total input rows |
| inserted_count | INTEGER NOT NULL | Successful row inserts |
| error_count | INTEGER NOT NULL | Failed row count |
| started_at | TEXT NOT NULL | Start time |
| completed_at | TEXT | Finish time |
| notes | TEXT | Summary or failure note |

Used by:

- Data Import/Settings page
- Import pipeline

## agent_runs

Purpose: execution trace for agent invocations.

| Column | Type | Notes |
| --- | --- | --- |
| id | TEXT PRIMARY KEY | Generated run ID |
| agent_name | TEXT NOT NULL | Agent or orchestrator name |
| trigger_type | TEXT NOT NULL | `dashboard`, `chat`, `map`, `product`, `report`, `refresh` |
| trigger_ref | TEXT | Related entity or request ID |
| status | TEXT NOT NULL | `running`, `completed`, `failed`, `partial` |
| started_at | TEXT NOT NULL | Start time |
| completed_at | TEXT | End time |
| input_ref | TEXT | Input summary or pointer |
| output_ref | TEXT | Output summary or pointer |
| error_message | TEXT | Failure details |
| duration_ms | INTEGER | Runtime |

Used by:

- Chat agent trace surfaces
- Debugging views
- Reporting Agent audit trail

## Enums And Status Rules

### Severity

- `1` Low
- `2` Guarded
- `3` Elevated
- `4` High
- `5` Critical

### Common status values

- Reports: `queued`, `running`, `completed`, `partial`, `failed`
- Imports: `queued`, `processing`, `completed`, `failed`
- Risk events: `open`, `monitoring`, `resolved`
- Agent runs: `running`, `completed`, `failed`, `partial`

## Page And Agent Coverage Summary

- `Dashboard`: products, suppliers, inventory_snapshots, fulfillment_snapshots, risk_events, country_risk_scores
- `Chat`: chat_sessions, chat_messages, products, suppliers, risk_events, reports, agent_runs
- `Map`: country_risk_scores, risk_events, suppliers, product_suppliers, products
- `Reports`: reports, risk_events, products, suppliers, country_risk_scores, agent_runs
- `Product Detail`: products, sales_history, inventory_snapshots, fulfillment_snapshots, product_suppliers, suppliers, risk_events
- `Data Import/Settings`: imports, agent_runs, reports for artifact path visibility, plus runtime health outside sqlite
