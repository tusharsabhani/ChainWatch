# PAGES

This document defines the six v1 pages for ChainWatch. Each page section includes purpose, layout, behavior, required APIs, and acceptance criteria so frontend and backend implementation can proceed without product ambiguity.

## Shared UI Rules

- All pages live in a `Next.js` App Router application.
- The top-level app shell includes left navigation, page title, and a right-side status area for global system health.
- Every page must support loading, empty, and error states.
- Every page must support a clear "last updated" surface for data freshness.
- Every page that shows risk must use the same severity scale:
  - `1` Low
  - `2` Guarded
  - `3` Elevated
  - `4` High
  - `5` Critical

## Dashboard

### Goal

Give the user an immediate operational summary of inventory, fulfillment, and external-risk pressure across the business.

### Primary user

`E-commerce Operations Manager`

### Route

`/`

### Layout

- KPI row at the top
- Left column for recent alerts and top-risk products
- Right column for top-risk suppliers and country exposure
- Bottom row for trend charts

### Widgets and components

- KPI cards
  - total active alerts
  - products at stockout risk
  - suppliers with active exposure
  - countries with active external issues
- Recent risk alerts table
- Top at-risk SKUs list
- Supplier exposure summary
- Trend charts
  - demand pressure over time
  - fulfillment SLA trend
  - external risk event count over time

### User actions

- Filter by date range
- Filter by severity threshold
- Filter by product category
- Filter by region
- Open a product detail page from a top-risk SKU
- Open a country panel from supplier exposure or external-risk summary

### Filters

- `dateRange`: `7d`, `30d`, `90d`
- `severityMin`: `1-5`
- `category`: optional
- `region`: optional

### Loading, empty, error states

- Loading shows KPI skeletons plus chart and table placeholders.
- Empty state explains that imports must be completed before the dashboard can render meaningful summaries.
- Error state shows the failing API group and offers a retry action.

### Required backend data

- Dashboard summary metrics
- Active alerts
- Trend series
- Top-risk products
- Top-risk suppliers
- Country exposure snapshot

### APIs consumed

- `GET /api/dashboard/summary`
- `GET /api/dashboard/alerts`

### Acceptance criteria

- The page renders a coherent operational overview from backend data only.
- Severity filters affect KPIs, alerts, and trend visuals consistently.
- Clicking a product takes the user to the product detail route.
- A country-linked risk card can open the Map page with a country context.

## Chat

### Goal

Let the user ask grounded questions about products, suppliers, countries, fulfillment status, and external disruptions and receive answers with citations.

### Primary user

`Retail Analyst`

### Route

`/chat`

### Layout

- Left rail for session list
- Main conversation panel
- Optional right rail for citations and agent trace summary

### Widgets and components

- Session list
- New chat button
- Conversation transcript
- Message composer
- Citation list
- Agent usage summary
- Optional context chips
  - product
  - supplier
  - country
  - report scope

### User actions

- Create a new session
- Continue an existing session
- Send a question
- Inspect citations
- Open a related product or country from the answer

### Filters and context

- Context scope is optional and may be:
  - `global`
  - `product`
  - `supplier`
  - `country`

### Loading, empty, error states

- Empty state prompts the user with sample questions.
- While a message is being answered, the UI shows the pending assistant turn.
- If the search provider is unavailable, the UI must still return an answer with a clear "external search unavailable" notice.

### Required backend data

- Session metadata
- Historical session messages
- Assistant answer payload with citations and used agents

### APIs consumed

- `GET /api/chat/sessions`
- `POST /api/chat/sessions`
- `GET /api/chat/sessions/{session_id}/messages`
- `POST /api/chat/messages`

### Acceptance criteria

- The user can start a session and ask a question without leaving the page.
- Responses include citation objects when external evidence is used.
- The UI indicates which agents contributed to the answer.
- Message history reloads correctly when reopening a session.

## Map

### Goal

Show country-level external-risk hotspots and let the user understand which suppliers and SKUs are exposed.

### Primary user

`Category Manager`

### Route

`/map`

### Layout

- Main map canvas
- Summary chips above the map
- Right-side country detail panel

### Widgets and components

- Country choropleth map using `React Simple Maps`
- Risk legend
- Country hover tooltip
- Country detail drawer or side panel
- Active issue list
- Exposed suppliers list
- Exposed SKUs list

### User actions

- Hover a country to see quick risk info
- Click a country to pin details
- Filter by risk type
- Filter by minimum severity
- Open a linked product detail page
- Open report generation for the selected country

### Filters

- `riskType`: `all`, `geopolitical`, `tariff`, `logistics`, `weather`, `labor`
- `severityMin`: `1-5`

### Loading, empty, error states

- Loading shows a skeleton for the map and country panel.
- Empty state says that no active country issues are present for the selected filter.
- Error state shows whether the failure is in the map summary feed or the country detail feed.

### Required backend data

- Country risk scores
- Active event counts
- Country detail including issue list, affected suppliers, and affected products

### APIs consumed

- `GET /api/map/countries`
- `GET /api/map/countries/{country_code}`

### Acceptance criteria

- Countries visually reflect risk intensity from backend data.
- Clicking a country updates the detail panel without leaving the page.
- Country detail includes at least one issue list and exposed entities section.
- The page can be linked into from Dashboard and Reports with a country preselection.

## Reports

### Goal

Let the user browse generated reports, inspect their contents, and trigger new report generation for key scopes.

### Primary user

`Operations Leadership`

### Route

`/reports`

### Layout

- Report list on the left or center
- Detail panel on the right or below
- Action bar for generation and filtering

### Widgets and components

- Report list table
- Status badges
- Scope filters
- Generated-at timestamp
- Markdown preview area
- Metadata panel
- Generate report action

### User actions

- Filter reports by scope type
- Filter by status
- Open a report
- Generate a new report
- Download or open the local Markdown path

### Filters

- `scopeType`: `dashboard`, `product`, `country`, `supplier`, `chat`
- `status`: `queued`, `running`, `completed`, `failed`

### Loading, empty, error states

- Empty state prompts the user to generate the first report.
- Reports with `failed` status show the failure reason if available.
- A running report should show progress messaging without blocking the rest of the page.

### Required backend data

- Report list
- Report metadata
- Report content locations
- Report generation status

### APIs consumed

- `GET /api/reports`
- `GET /api/reports/{report_id}`
- `POST /api/reports/generate`

### Acceptance criteria

- The page can list existing reports and open details for one report at a time.
- A generated report stores both JSON and Markdown output paths.
- The detail view can render Markdown content or a preview summary from backend response data.

## Product Detail

### Goal

Provide a SKU-level view that combines sales trend, inventory health, supplier exposure, fulfillment status, and linked risk events.

### Primary user

`Inventory Planner`

### Route

`/products/[productId]`

### Layout

- Product header and core status row
- Tabs or stacked sections for demand, inventory, fulfillment, suppliers, and risk events

### Widgets and components

- Product summary card
- Demand trend chart
- Inventory health card
- Supplier exposure table
- Fulfillment status card
- Linked risk events list
- Quick actions
  - ask in chat
  - generate report
  - open supplier or country context

### User actions

- Change time range
- Filter by region
- Open a linked risk event source
- Start a contextual chat
- Generate a product report

### Filters

- `dateRange`: `30d`, `90d`, `365d`
- `region`: optional
- `channel`: optional

### Loading, empty, error states

- Loading shows chart and card placeholders.
- Empty state explains whether the product exists but lacks sales or inventory history.
- Error state points to the product API response and keeps the page shell intact.

### Required backend data

- Product metadata
- Historical sales aggregates
- Latest inventory snapshot
- Supplier list and supplier exposure
- Fulfillment summary
- Linked risk events

### APIs consumed

- `GET /api/products`
- `GET /api/products/{product_id}`
- `POST /api/reports/generate`

### Acceptance criteria

- The page gives a single-product view without requiring the user to cross-reference other pages.
- Demand, inventory, and fulfillment sections all use the same product identifier.
- Risk events and supplier exposure are visible in the same screen.

## Data Import/Settings

### Goal

Let the user load local data and confirm system readiness, provider availability, and storage paths.

### Primary user

`Retail Analyst`

### Route

`/settings`

### Layout

- Runtime status cards at the top
- Import panels in the middle
- Local storage and provider section at the bottom

### Widgets and components

- Health card
- Database status card
- Provider status card
- Import forms
  - sales
  - inventory
  - suppliers
  - products
- Recent imports list
- Storage paths panel

### User actions

- Upload a CSV for an import type
- Review import status and summary counts
- See current local data paths
- See whether the LLM and search adapters are configured

### Filters

- Import history filter by type
- Import history filter by status

### Loading, empty, error states

- Empty state encourages the user to import base data before visiting product pages.
- If the health endpoint is available but providers are not configured, the page must show a warning rather than a hard failure.
- Import errors must show row-count summary and a clear next step.

### Required backend data

- System health and runtime configuration summary
- Recent import history
- Import result payloads

### APIs consumed

- `GET /api/health`
- `GET /api/imports`
- `POST /api/imports/products`
- `POST /api/imports/sales`
- `POST /api/imports/inventory`
- `POST /api/imports/suppliers`

### Acceptance criteria

- A user can inspect system readiness without reading logs.
- Each import type has a dedicated action and clear success/error feedback.
- The page surfaces the configured provider placeholders and local storage paths.
