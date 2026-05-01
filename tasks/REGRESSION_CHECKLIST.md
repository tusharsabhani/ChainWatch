# REGRESSION CHECKLIST

Use this checklist when verifying ChainWatch after backend changes. It mirrors the contracts in `API_SPEC.md` and the implementation phases in `tasks/BACKEND_IMPLEMENTATION_PLAN.md`.

## Runtime

- [ ] `GET /api/health` returns `ok` with database, storage, provider, and background-task readiness
- [ ] Local demo data can be seeded and imported without errors

## Dashboard

- [ ] `GET /api/dashboard/summary` returns KPIs, top-risk products, country exposure, trends, and freshness metadata
- [ ] `GET /api/dashboard/alerts` returns active alerts filtered by severity and status

## Map

- [ ] `GET /api/map/countries` returns country coloring data plus freshness metadata
- [ ] `GET /api/map/countries/{country_code}` returns issues, affected suppliers, and affected products for a known country

## Products

- [ ] `GET /api/products` returns searchable product list results with risk scores
- [ ] `GET /api/products/{product_id}` returns demand, inventory, fulfillment, supplier, and linked-risk sections

## Chat

- [ ] `POST /api/chat/sessions` creates a reusable session
- [ ] `POST /api/chat/messages` persists the user message and returns an assistant answer with `usedAgents` and citations
- [ ] `GET /api/chat/sessions/{session_id}/messages` returns ordered history for the same session

## Reports

- [ ] `POST /api/reports/generate` returns a queued report ID
- [ ] `GET /api/reports/{report_id}` eventually returns artifact paths, preview content, and report freshness metadata
- [ ] Chat export and country/product report scopes can both be generated

## Imports

- [ ] `GET /api/imports` shows recent runs and statuses
- [ ] Import endpoints accept a valid local `filePath` payload and create a new run
- [ ] Invalid import paths return the shared error shape

## Reliability

- [ ] Cached external-risk responses can still serve dashboard/map/product flows
- [ ] Stale cached external-risk responses surface freshness metadata and schedule a background refresh when search is configured
- [ ] Report generation can be queued without breaking subsequent list and detail reads

## Cross-Surface Consistency

- [ ] A top-risk product from Dashboard loads the same SKU and name in Product Detail
- [ ] A country highlighted on Map returns matching issue context in country detail
- [ ] A chat session can be exported as a chat-scoped report
