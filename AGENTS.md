# AGENTS

This document defines the backend agent system for ChainWatch. Each agent must operate on normalized data structures and return explicit, inspectable outputs. Agent orchestration should favor determinism and traceability over novelty.

## Common Agent Design

Every agent should expose:

- a clear purpose
- a trigger path
- a structured input contract
- a structured output contract
- tool access boundaries
- fallback behavior
- trace metadata suitable for `agent_runs`

Every agent output should be machine-readable first and user-facing second.

## Shared Severity Scale

- `1` Low
- `2` Guarded
- `3` Elevated
- `4` High
- `5` Critical

## External Risk Agent

### Purpose

Track external disruptions that may affect suppliers, routes, inventory availability, landed cost, or fulfillment outcomes.

### Trigger paths

- Map summary refresh
- Country detail request
- Dashboard alert refresh
- Product detail when supplier-country exposure is requested
- Chat questions involving countries, suppliers, tariffs, shipping, or disruptions
- Report generation for dashboard, country, supplier, or product scope

### Inputs

- country codes
- supplier countries
- route hints when available
- product category or supplier scope
- freshness policy
- recent cached events

### Tools

- `SearchAdapter`
- citation normalization helper
- cache reader/writer
- sqlite read/write for risk events and country scores

### Output

Structured output should include:

- `risk_events[]`
- `country_scores[]`
- `citations[]`
- `summary`
- `highest_severity`
- `affected_suppliers[]`
- `affected_products[]`

### Failure and fallback behavior

- If live search fails, return cached results if available.
- If no cached results exist, return an empty result with an explicit limitation flag.
- Never fabricate citations.

### UI and report surfacing

- Colors countries on the Map page
- Powers Dashboard external-risk summaries
- Appears in product-linked risk events
- Provides cited evidence in Chat
- Contributes issue sections to generated reports

## Demand Agent

### Purpose

Analyze `3-5 years` of sales history to identify seasonality, demand spikes, product velocity, and forecasted stockout pressure.

### Trigger paths

- Product detail load
- Dashboard summary refresh
- Chat questions about demand, seasonality, or forecasted risk
- Report generation for product or dashboard scope

### Inputs

- product ID or product set
- `3-5 years` of sales history
- optional region filter
- optional channel filter
- recent stockout flags
- promo flags

### Tools

- sqlite query layer
- aggregation service
- `LLMAdapter` only for narrative summarization when needed

### Output

Structured output should include:

- `historical_trend`
- `seasonal_windows[]`
- `recent_spikes[]`
- `forecast_window_days`
- `forecasted_units`
- `demand_risk_score`
- `supporting_notes`

### Failure and fallback behavior

- If fewer than `12 months` of sales history are available, mark the result as low-confidence.
- If the LLM is unavailable, still return deterministic aggregates and risk scoring.

### UI and report surfacing

- Powers Dashboard demand trend visuals
- Powers Product Detail demand section
- Supports stockout reasoning in Chat
- Feeds demand sections in product and dashboard reports

## Inventory Agent

### Purpose

Measure current stock health, reorder urgency, safety-stock pressure, and stockout probability from inventory position.

### Trigger paths

- Dashboard summary refresh
- Product detail load
- Chat questions about stock levels or reorder urgency
- Report generation for dashboard or product scope

### Inputs

- current inventory snapshots
- inbound quantities
- reorder points
- safety stock
- days of cover
- product demand summary from Demand Agent when available

### Tools

- sqlite query layer
- risk scoring utilities

### Output

Structured output should include:

- `current_on_hand`
- `reserved_qty`
- `inbound_qty`
- `days_of_cover`
- `reorder_point`
- `stockout_risk_score`
- `inventory_status`
- `recommended_action`

### Failure and fallback behavior

- If inbound data is missing, do not block the result; mark the recommendation as partial.
- If demand data is unavailable, compute inventory risk from static thresholds and label it accordingly.

### UI and report surfacing

- Contributes KPI counts and top-risk SKU logic on Dashboard
- Powers Product Detail inventory section
- Supports product and dashboard reports
- Informs Chat when users ask what is at risk right now

## Fulfillment Agent

### Purpose

Evaluate fulfillment health by combining regional backlog, warehouse delay, on-time rate, and external disruption exposure.

### Trigger paths

- Dashboard summary refresh
- Product detail load
- Chat questions about SLA risk or delivery issues
- Report generation for dashboard, product, or country scope

### Inputs

- fulfillment snapshots
- warehouse and region data
- order backlog metrics
- average ship delay
- on-time rate
- relevant external-risk events

### Tools

- sqlite query layer
- optional dependency on External Risk Agent outputs

### Output

Structured output should include:

- `regional_status[]`
- `backlog_orders`
- `avg_ship_delay_hours`
- `on_time_rate`
- `fulfillment_risk_score`
- `sla_risk_level`
- `recommended_action`

### Failure and fallback behavior

- If fulfillment snapshots are missing, return a partial result with a data-gap note.
- If external-risk enrichment fails, keep local warehouse metrics and note missing external context.

### UI and report surfacing

- Feeds Dashboard fulfillment KPIs and trend charts
- Powers Product Detail fulfillment section
- Supports Chat answers about delivery impact
- Contributes operational impact sections in reports

## Reporting Agent

### Purpose

Turn consolidated risk findings into structured report artifacts that are easy to inspect locally and easy to share with stakeholders.

### Trigger paths

- Explicit report generation request
- Optional downstream use from a chat answer or product quick action

### Inputs

- report scope
- scope identifier
- relevant agent outputs
- citations
- metadata such as generation time and status

### Tools

- local filesystem writer
- markdown renderer
- report serializer
- sqlite write access for report metadata

### Output

Structured output should include:

- `report_json`
- `report_markdown`
- `summary`
- `artifact_paths`
- `generation_status`

### Failure and fallback behavior

- If Markdown rendering fails after JSON is produced, keep the report in `failed` or `partial` status with the JSON artifact preserved.
- If agent data is incomplete, the report must include a visible limitations section.

### UI and report surfacing

- Powers the Reports page
- Supports quick actions from Product Detail and Map
- Stores outputs that can later be opened from the filesystem

## Chat Orchestrator

### Purpose

Route user questions to the right agents, merge structured findings, preserve citations, and return one coherent answer.

### Trigger paths

- Any user message posted to a chat session

### Inputs

- session context
- user message
- optional scoped entity such as product or country
- recent conversation history

### Tools

- session storage
- intent classification helper
- all domain agents
- `LLMAdapter` for final response composition

### Output

Structured output should include:

- `assistant_message`
- `used_agents[]`
- `citations[]`
- `scope`
- `limitations[]`
- `agent_trace_summary`

### Failure and fallback behavior

- If one agent fails, continue with the remaining agents when possible.
- If the LLM is unavailable, return a concise structured answer assembled from deterministic outputs.
- If citations are unavailable, do not imply that external validation occurred.

### UI and report surfacing

- Directly powers the Chat page
- Provides agent trace metadata for debugging
- Can hand off the same gathered context to the Reporting Agent when a report is requested from chat

## Agent Coordination Patterns

### Dashboard summary

- `Demand Agent`
- `Inventory Agent`
- `Fulfillment Agent`
- `External Risk Agent`

### Product detail

- `Demand Agent`
- `Inventory Agent`
- `Fulfillment Agent`
- `External Risk Agent` when supplier-country exposure exists

### Map

- `External Risk Agent`

### Reports

- `Reporting Agent` plus whichever domain agents match the scope

### Chat

- `Chat Orchestrator` with one or more domain agents

## Traceability Rules

- Every agent invocation should create an `agent_runs` entry.
- Every agent output should identify whether it used cached or fresh external data.
- Every user-facing answer or report section that depends on search results must preserve citation links.
