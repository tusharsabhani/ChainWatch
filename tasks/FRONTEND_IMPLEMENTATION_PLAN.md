# FRONTEND IMPLEMENTATION PLAN

This file is the execution-oriented frontend tracker for ChainWatch.

It is a companion to:

- `tasks/STATUS.md` for official task state
- `tasks/FRONTEND_TASKS.md` for task definitions and acceptance criteria
- `tasks/DECISIONS.md` for implementation decisions
- `PAGES.md` for page behavior, layout, and API usage

`tasks/STATUS.md` remains the source of truth for `Todo`, `In Progress`, `Blocked`, and `Done`.

## Purpose

Use this file to:

- group frontend work into delivery phases
- track what is implemented and what is still missing
- sequence page and shared-client work in a practical order
- capture evidence and notes as implementation progresses

## Current Snapshot

| Area | Status | Notes |
| --- | --- | --- |
| Frontend codebase | Phase 3 implemented | `frontend/` now includes both live core read pages and workflow surfaces on top of the standalone Next.js App Router project |
| Backend APIs | Implemented | Backend phases are complete through reliability and scenario coverage |
| Shared API client | Implemented | Typed fetch helpers now cover health, dashboard, map, products, chat, reports, and imports |
| Shell and routing | Implemented | The app shell now follows the Stitch mock system with a dark desktop rail, compact top bar, and route-aware mobile shells |
| Pages | Phase 3 implemented | Dashboard, Map, Product Detail, Chat, Reports, and Settings/Imports now all have live frontend workflows |
| Frontend validation | Implemented | `npm install` completed, workflow route handlers were added, and `npm run build` passed |

## Working Rules

1. Keep `tasks/STATUS.md` as the official state board.
2. Update this file as phases and task checkpoints move forward.
3. Reuse the backend API contracts from `API_SPEC.md` instead of inventing frontend-only data shapes.
4. Build shared API, loading, error, and freshness handling early so page work stays consistent.
5. Favor one-page-complete slices over scattered partial UI across many routes.

## Phase 1: Frontend Foundation

This phase creates the application shell and the shared frontend data primitives that every page will use.

### FE-01 App Shell, Routing, Navigation, And Theme

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | High |
| Depends on | None |
| Goal | Create the Next.js app shell, route scaffolds, and shared visual foundation |

Implementation checkpoints:

- [x] Create `frontend/` project root
- [x] Create Next.js App Router application
- [x] Add global layout with left navigation and top status area
- [x] Add route scaffolds for all v1 pages
- [x] Add shared theme tokens, typography, spacing, and severity colors
- [x] Add page title and breadcrumb pattern
- [x] Make the shell responsive on desktop and mobile

Definition of done:

- [x] A user can navigate to all planned routes without broken links
- [x] The shell can host runtime status and page-level content consistently
- [x] Theme primitives are ready for all later page work

Evidence:

- `frontend/` now contains a standalone Next.js App Router scaffold with a Stitch-aligned shell, responsive navigation, and route-aware mobile behavior
- The shell uses a dark fixed desktop rail, a compact white top app bar, a focused mobile chat shell, and bottom-tab mobile navigation for the standard surfaces
- Shared theme tokens, typography, severity colors, and shell spacing live in `frontend/app/globals.css` and `frontend/tailwind.config.ts`

### FE-08 Shared API Client, Loading States, And Error States

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | High |
| Depends on | `FE-01`, `BE-11`, `BE-12` |
| Goal | Centralize data fetching and unify loading, error, retry, and freshness behavior |

Implementation checkpoints:

- [x] Create shared API client utilities
- [x] Add shared request and response typing aligned to `API_SPEC.md`
- [x] Add common loading and error components
- [x] Add shared retry and empty-state patterns
- [x] Add shared handling for `lastUpdatedAt` and `freshness` metadata
- [x] Add page-level fetch helpers or hooks for backend endpoints

Definition of done:

- [x] All page data access can go through shared frontend utilities
- [x] Loading and error handling follow one consistent pattern
- [x] Freshness metadata is rendered consistently across surfaces

Evidence:

- `frontend/lib/api/` now contains a shared client plus typed helpers for every backend endpoint group
- Shared `LoadingState`, `ErrorState`, `EmptyState`, `RetryButton`, and `FreshnessBadge` components are available across the app in the same compact visual system as the page mocks
- The settings page uses the shared client to render live health and import-history previews from backend APIs, while the global shell heartbeat is server-fetched from `GET /api/health`
- `npm run build` passes for the scaffolded frontend project after dependency installation

## Phase 2: Core Read Pages

This phase focuses on the main read-only operational surfaces so the app becomes visibly useful early.

### FE-02 Dashboard Page

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | High |
| Depends on | `FE-01`, `FE-08`, `BE-11` |
| Goal | Build the operational overview page from dashboard summary and alerts APIs |

Implementation checkpoints:

- [x] Create KPI card row
- [x] Create alerts table
- [x] Create top-risk products and suppliers sections
- [x] Create trend chart sections
- [x] Add date range, severity, category, and region filters
- [x] Add loading, empty, and error states

Definition of done:

- [x] The page renders a complete dashboard from live backend responses
- [x] Filters update KPI, alert, and trend sections consistently
- [x] Product links route to the Product Detail page

Evidence:

- `frontend/app/page.tsx` now loads live summary and alert data from backend APIs, renders filters through query params, and links ranked products into the live Product Detail route
- The dashboard shows graceful empty-state behavior when external-risk providers are unconfigured, while still surfacing demand, fulfillment, and product-risk data from the seeded local dataset

### FE-06 Product Detail Page

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | High |
| Depends on | `FE-01`, `FE-08`, `BE-11` |
| Goal | Build a single-product page from one product-detail payload |

Implementation checkpoints:

- [x] Create product summary header
- [x] Create demand section
- [x] Create inventory section
- [x] Create fulfillment section
- [x] Create supplier exposure section
- [x] Create linked risk events section
- [x] Add quick actions for chat and report generation

Definition of done:

- [x] The page renders from a single product detail payload
- [x] Each major section shares the same product context
- [x] Quick actions route or trigger the expected downstream behavior

Evidence:

- `frontend/app/products/[productId]/page.tsx` now loads the live product detail payload, supports date-range toggles, and renders demand, inventory, fulfillment, supplier, and linked-risk sections from one backend response
- Quick actions now route into Chat and Reports with product scope in the query string, and invalid product IDs fall back to a live product suggestion list instead of a dead-end shell

### FE-04 Map Page

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | High |
| Depends on | `FE-01`, `FE-08`, `BE-11` |
| Goal | Build the country-risk map and country detail flow |

Implementation checkpoints:

- [x] Create `React Simple Maps` world view
- [x] Create risk legend and hover tooltip
- [x] Create country selection and detail panel
- [x] Add risk type and minimum severity filters
- [x] Add links from country detail to products and report generation
- [x] Add loading, empty, and error states

Definition of done:

- [x] Countries are colored from backend risk scores
- [x] Clicking a country loads issues, suppliers, and products
- [x] Filters update the rendered country set without breaking selection

Evidence:

- `frontend/components/world-risk-map.tsx` now renders a `react-simple-maps` world view backed by `world-atlas`, with hover detail and query-param selection
- `frontend/app/map/page.tsx` now wires risk-type and severity filters to the backend map APIs and falls back to seeded supplier-country coverage when no external-risk scores are available yet

## Phase 3: Workflow Pages

This phase adds the interactive workflows that sit on top of the completed backend orchestration and API layers.

### FE-05 Reports List And Detail Page

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | Medium |
| Depends on | `FE-01`, `FE-08`, `BE-12` |
| Goal | Build report browsing, report detail, and report generation UI |

Implementation checkpoints:

- [x] Create reports list table
- [x] Add status and scope filtering
- [x] Create report detail panel with metadata and Markdown preview
- [x] Add generate report action
- [x] Add queued, running, completed, failed, and empty states

Definition of done:

- [x] A user can browse reports and open one report at a time
- [x] The page distinguishes report status values clearly
- [x] Markdown preview or summary content is visible for completed reports

Evidence:

- `frontend/app/reports/page.tsx` now renders the live report archive, selected detail, and generator defaults from route query context
- `frontend/components/reports/reports-workspace.tsx` now supports status/scope filters, report generation, queued/running polling, artifact metadata, and Markdown preview rendering from the backend

### FE-03 Chat Page

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | Medium |
| Depends on | `FE-01`, `FE-08`, `BE-12` |
| Goal | Build the chat experience with sessions, transcript, citations, and agent usage |

Implementation checkpoints:

- [x] Create session list panel
- [x] Create new chat flow
- [x] Create message list and composer
- [x] Render citations and used-agent metadata
- [x] Add context chip support for product or country scope
- [x] Add loading, pending, empty, and error states

Definition of done:

- [x] A user can create a session and send a message
- [x] Responses render citations and used-agent metadata when available
- [x] Existing sessions reload and render history correctly

Evidence:

- `frontend/app/chat/page.tsx` now hydrates the chat workspace from live backend sessions and conversation history, with query-seeded scope support for product and country handoffs
- `frontend/components/chat/chat-workspace.tsx` now handles session creation, transcript rendering, composer posting, citations, used-agent metadata, and same-origin interactive loading states

### FE-07 Data Import And Settings Page

| Field | Value |
| --- | --- |
| Status | Done |
| Priority | Medium |
| Depends on | `FE-01`, `FE-08`, `BE-12` |
| Goal | Build the operational page for runtime health, provider readiness, and import activity |

Implementation checkpoints:

- [x] Create runtime health cards
- [x] Create provider status section
- [x] Create local storage paths section
- [x] Create import forms for products, sales, inventory, and suppliers
- [x] Create recent imports list with status summary
- [x] Add warnings and failure states for provider and import issues

Definition of done:

- [x] A user can inspect runtime readiness and recent imports from one screen
- [x] Each import type has a dedicated UI action
- [x] Import success and failure responses are clearly visible

Evidence:

- `frontend/app/settings/page.tsx` now surfaces operational warning banners, provider readiness, storage paths, and recent import history from live backend data
- `frontend/components/settings/import-control-panel.tsx` now provides dedicated local-path import actions for products, sales, inventory, and suppliers, with success/error banners and refresh behavior

## Suggested First Execution Sequence

1. Build `FE-01` to create the frontend project, routes, shell, and theme.
2. Build the shared client and state-handling layer in `FE-08`.
3. Implement `FE-02` Dashboard first to validate the shared API client against the most important overview page.
4. Implement `FE-06` Product Detail next because it is a focused, single-entity surface with strong backend support.
5. Implement `FE-04` Map after product detail so country-to-product linking can reuse existing page patterns.
6. Implement `FE-05` Reports and `FE-03` Chat once the core read pages are stable.
7. Implement `FE-07` Data Import And Settings after the shared health/import patterns are already established elsewhere in the app.

## Notes

- `FE-08` is intentionally placed in phase 1 even though its task number is later; it is a shared prerequisite in practice.
- The backend is already complete enough for live frontend wiring, so frontend phases can focus on UX and integration rather than backend gaps.
- Favor finishing one route end-to-end, including loading and error states, before starting too many parallel page builds.
