# FRONTEND TASKS

Each task below is a complete frontend step. A step should close a page or a shared frontend capability in a usable state. Do not mark a task done until its acceptance criteria are met and `tasks/STATUS.md` is updated.

## FE-01 App Shell, Routing, Navigation, And Theme

### Goal

Create the frontend foundation for the Next.js application.

### Deliverables

- App Router setup
- Global layout with left navigation and top status area
- Route scaffolds for all six v1 pages
- Shared theme tokens, typography, spacing, and severity color usage
- Basic page title and breadcrumb pattern

### Dependencies

- None

### Acceptance criteria

- A user can navigate to all planned routes without broken links.
- The shell can visually host a runtime status indicator.
- Theme primitives are ready for all later page work.

## FE-02 Dashboard Page

### Goal

Implement the dashboard UI and wire it to dashboard summary and alerts APIs.

### Deliverables

- KPI card row
- Alerts table
- Top-risk products and suppliers sections
- Trend chart sections
- Date range, severity, category, and region filters
- Empty, loading, and error states

### Dependencies

- `FE-01`
- `BE-11`

### Acceptance criteria

- The page renders a complete dashboard from live backend responses.
- Filters update the visible dashboard sections consistently.
- Product links route to the Product Detail page.

## FE-03 Chat Page

### Goal

Implement the chat experience with session list, transcript, composer, citations, and agent usage summary.

### Deliverables

- Session list panel
- New chat flow
- Message list and composer
- Citation rendering
- Used-agents summary
- Context chip support for product or country scope
- Loading, pending, empty, and error states

### Dependencies

- `FE-01`
- `BE-10`
- `BE-12`

### Acceptance criteria

- A user can create a session and send a message.
- Responses render citations and used-agent metadata when available.
- Existing sessions reload and render message history correctly.

## FE-04 Map Page

### Goal

Implement the world map experience for country-level risk monitoring.

### Deliverables

- `React Simple Maps` world view
- Risk legend
- Country hover tooltip
- Country selection and detail panel
- Filters for risk type and minimum severity
- Links from country detail to products and report generation

### Dependencies

- `FE-01`
- `BE-05`
- `BE-11`

### Acceptance criteria

- Countries are colored from backend risk scores.
- Clicking a country loads a detail panel with issues, suppliers, and products.
- Filters update the rendered country set without breaking selection.

## FE-05 Reports Generation Page

### Goal

Implement the Reports page as a report-generation workflow.

### Deliverables

- Generate report action
- Scope selector and optional title input
- Success, loading, and error states for report generation

### Dependencies

- `FE-01`
- `BE-09`
- `BE-12`

### Acceptance criteria

- A user can submit a report-generation request for supported scopes.
- The page shows the queued report ID and returned status after a successful request.
- The docs do not claim report list/detail browsing until that UI exists.

## FE-06 Product Detail Page

### Goal

Implement a single-product page with demand, inventory, fulfillment, suppliers, and linked risk events.

### Deliverables

- Product summary header
- Demand trend section
- Inventory health section
- Fulfillment section
- Supplier exposure section
- Linked risk events section
- Quick actions for chat and report generation

### Dependencies

- `FE-01`
- `BE-06`
- `BE-07`
- `BE-08`
- `BE-11`

### Acceptance criteria

- The page renders from a single product detail payload.
- Each major section shares the same product context.
- Quick actions route or trigger the expected downstream behavior.

## FE-07 Data Import And Settings Page

### Goal

Implement the operational settings page for imports, runtime status, and provider readiness.

### Deliverables

- Runtime health cards
- Provider status section
- Local storage paths section
- Import forms for products, sales, inventory, and suppliers
- Recent imports list with status summary
- Warning and error surfaces for unconfigured providers or failed imports

### Dependencies

- `FE-01`
- `BE-04`
- `BE-12`

### Acceptance criteria

- A user can inspect runtime readiness and recent imports from one screen.
- Each import type has a dedicated UI action.
- Import success and failure responses are clearly visible.

## FE-08 Shared API Client, Loading States, And Error States

### Goal

Unify data fetching and standardize frontend state handling across all pages.

### Deliverables

- Shared API client utilities
- Shared request and response typing
- Consistent loading and error components
- Common handling for stale data timestamps and retry states
- Page-level data hooks or fetch helpers aligned to the API spec

### Dependencies

- `FE-01`
- `BE-11`
- `BE-12`

### Acceptance criteria

- All page data access goes through shared frontend utilities.
- Loading and error handling follow a consistent visual pattern.
- Timestamp and freshness metadata are displayed the same way across pages.
