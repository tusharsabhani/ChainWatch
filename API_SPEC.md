# API SPEC

This document defines the backend REST contract for ChainWatch. All frontend pages must consume backend data through these endpoints. Response shapes below are representative contracts for v1 and should remain stable unless the docs are updated together.

## Common Conventions

- Base path: `/api`
- Content type: `application/json`
- Time values use ISO 8601 strings in UTC
- Errors return a consistent shape:

```json
{
  "error": {
    "code": "string_code",
    "message": "Human-readable message",
    "details": {}
  }
}
```

- Successful responses may include `lastUpdatedAt` when the payload depends on cached or computed data.
- Cached or computed responses may also include a `freshness` object:

```json
{
  "freshness": {
    "dataSource": "fresh",
    "lastUpdatedAt": "2026-04-23T12:00:00Z",
    "cacheUpdatedAt": "2026-04-23T12:00:00Z",
    "isStale": false,
    "refreshScheduled": false
  }
}
```

## Health And Runtime

### GET /api/health

Purpose: return runtime readiness, local storage status, and provider availability for the app shell and Settings page.

Consumed by:

- `Data Import/Settings`
- global app shell status area

Response shape:

```json
{
  "status": "ok",
  "appVersion": "0.1.0",
  "database": {
    "status": "connected",
    "path": "data/app.db"
  },
  "storage": {
    "reportsJsonPath": "data/reports/json",
    "reportsMarkdownPath": "data/reports/markdown",
    "importsPath": "data/imports/raw",
    "cachePath": "data/cache/external_risk"
  },
  "providers": {
    "llmConfigured": false,
    "searchConfigured": false
  },
  "backgroundTasks": {
    "reportsEnabled": true,
    "externalRiskRefreshEnabled": true
  }
}
```

Common errors:

- `health_unavailable`

## Dashboard

### GET /api/dashboard/summary

Purpose: return the main KPI and trend payload for the Dashboard page.

Query params:

- `dateRange`: `7d`, `30d`, `90d`
- `severityMin`: integer `1-5`
- `category`: optional string
- `region`: optional string

Consumed by:

- `Dashboard`

Response shape:

```json
{
  "filters": {
    "dateRange": "30d",
    "severityMin": 3,
    "category": null,
    "region": null
  },
  "kpis": {
    "activeAlerts": 12,
    "productsAtRisk": 8,
    "suppliersExposed": 5,
    "countriesWithIssues": 4
  },
  "topRiskProducts": [
    {
      "productId": 101,
      "sku": "SKU-101",
      "name": "Example Product",
      "riskScore": 4.2,
      "primaryRiskDriver": "inventory"
    }
  ],
  "topRiskSuppliers": [
    {
      "supplierId": 12,
      "name": "Supplier A",
      "countryCode": "CN",
      "riskScore": 4.0,
      "activeIssueCount": 3
    }
  ],
  "countryExposure": [
    {
      "countryCode": "CN",
      "overallScore": 4.1,
      "activeEventCount": 3
    }
  ],
  "trends": {
    "demandPressure": [],
    "slaRisk": [],
    "externalEventCount": []
  },
  "lastUpdatedAt": "2026-04-23T12:00:00Z",
  "freshness": {
    "dataSource": "fresh",
    "lastUpdatedAt": "2026-04-23T12:00:00Z",
    "cacheUpdatedAt": "2026-04-23T12:00:00Z",
    "isStale": false,
    "refreshScheduled": false
  }
}
```

Common errors:

- `dashboard_summary_unavailable`
- `invalid_filter`

### GET /api/dashboard/alerts

Purpose: return active alert rows for the Dashboard alert table.

Query params:

- `severityMin`: integer `1-5`
- `status`: optional `open`, `monitoring`, `resolved`
- `limit`: optional integer, default `25`

Consumed by:

- `Dashboard`

Response shape:

```json
{
  "items": [
    {
      "eventId": "evt_123",
      "title": "Port disruption affecting inbound shipments",
      "riskType": "logistics",
      "severity": 4,
      "countryCode": "SG",
      "affectedSupplierId": 12,
      "affectedProductId": 101,
      "status": "open",
      "detectedAt": "2026-04-23T10:00:00Z"
    }
  ],
  "total": 1,
  "lastUpdatedAt": "2026-04-23T12:00:00Z",
  "freshness": {
    "dataSource": "cached",
    "lastUpdatedAt": "2026-04-23T12:00:00Z",
    "cacheUpdatedAt": "2026-04-23T11:45:00Z",
    "isStale": false,
    "refreshScheduled": false
  }
}
```

Common errors:

- `dashboard_alerts_unavailable`

## Chat

### GET /api/chat/sessions

Purpose: return recent chat sessions for the session list.

Consumed by:

- `Chat`

Response shape:

```json
{
  "items": [
    {
      "id": "chat_001",
      "title": "Why are APAC delays rising?",
      "contextScope": "global",
      "contextId": null,
      "updatedAt": "2026-04-23T11:55:00Z"
    }
  ]
}
```

Common errors:

- `chat_sessions_unavailable`

### POST /api/chat/sessions

Purpose: create a new chat session.

Consumed by:

- `Chat`

Request shape:

```json
{
  "title": "Optional title",
  "contextScope": "global",
  "contextId": null
}
```

Response shape:

```json
{
  "id": "chat_002",
  "title": "Optional title",
  "contextScope": "global",
  "contextId": null,
  "createdAt": "2026-04-23T12:01:00Z"
}
```

Common errors:

- `invalid_context_scope`
- `chat_session_create_failed`

### GET /api/chat/sessions/{session_id}/messages

Purpose: return ordered messages for a session.

Consumed by:

- `Chat`

Response shape:

```json
{
  "session": {
    "id": "chat_001",
    "title": "Why are APAC delays rising?"
  },
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "messageText": "Why are APAC delays rising?",
      "createdAt": "2026-04-23T11:50:00Z"
    },
    {
      "id": "msg_002",
      "role": "assistant",
      "messageText": "APAC delays are rising because...",
      "citations": [],
      "usedAgents": [
        "External Risk Agent",
        "Fulfillment Agent"
      ],
      "createdAt": "2026-04-23T11:50:02Z"
    }
  ]
}
```

Common errors:

- `chat_session_not_found`

### POST /api/chat/messages

Purpose: persist a user message, invoke the orchestrator, and return the assistant response.

Consumed by:

- `Chat`

Request shape:

```json
{
  "sessionId": "chat_001",
  "message": "Which SKUs are most exposed to tariff risk this week?"
}
```

Response shape:

```json
{
  "userMessage": {
    "id": "msg_010",
    "role": "user",
    "messageText": "Which SKUs are most exposed to tariff risk this week?"
  },
  "assistantMessage": {
    "id": "msg_011",
    "role": "assistant",
    "messageText": "The most exposed SKUs are...",
    "usedAgents": [
      "External Risk Agent",
      "Inventory Agent"
    ],
    "citations": [
      {
        "title": "Source title",
        "url": "https://example.com",
        "sourceName": "Example Source"
      }
    ],
    "limitations": []
  }
}
```

Common errors:

- `chat_session_not_found`
- `chat_processing_failed`
- `search_provider_unavailable`

## Map

### GET /api/map/countries

Purpose: return the country summary payload used to color the map.

Query params:

- `riskType`: optional risk type filter
- `severityMin`: integer `1-5`

Consumed by:

- `Map`

Response shape:

```json
{
  "items": [
    {
      "countryCode": "CN",
      "countryName": "China",
      "overallScore": 4.1,
      "highestSeverity": 4,
      "activeEventCount": 3
    }
  ],
  "lastUpdatedAt": "2026-04-23T12:00:00Z",
  "freshness": {
    "dataSource": "fresh",
    "lastUpdatedAt": "2026-04-23T12:00:00Z",
    "cacheUpdatedAt": "2026-04-23T12:00:00Z",
    "isStale": false,
    "refreshScheduled": false
  }
}
```

Common errors:

- `country_scores_unavailable`

### GET /api/map/countries/{country_code}

Purpose: return the right-side detail panel payload for a selected country.

Consumed by:

- `Map`

Response shape:

```json
{
  "country": {
    "countryCode": "CN",
    "countryName": "China",
    "overallScore": 4.1,
    "summary": "Elevated logistics and tariff risk."
  },
  "issues": [
    {
      "eventId": "evt_123",
      "title": "Tariff change affecting imports",
      "riskType": "tariff",
      "severity": 4,
      "sourceUrl": "https://example.com"
    }
  ],
  "affectedSuppliers": [
    {
      "supplierId": 12,
      "name": "Supplier A"
    }
  ],
  "affectedProducts": [
    {
      "productId": 101,
      "sku": "SKU-101",
      "name": "Example Product"
    }
  ],
  "lastUpdatedAt": "2026-04-23T12:00:00Z",
  "freshness": {
    "dataSource": "cached",
    "lastUpdatedAt": "2026-04-23T12:00:00Z",
    "cacheUpdatedAt": "2026-04-23T11:40:00Z",
    "isStale": true,
    "refreshScheduled": true
  }
}
```

Common errors:

- `country_not_found`
- `country_detail_unavailable`

## Products

### GET /api/products

Purpose: return product search results used for linking and navigation.

Query params:

- `query`: optional text search
- `category`: optional string
- `riskMin`: optional numeric threshold
- `limit`: optional integer, default `25`

Consumed by:

- `Product Detail` entry flow
- `Chat` contextual linking

Response shape:

```json
{
  "items": [
    {
      "productId": 101,
      "sku": "SKU-101",
      "name": "Example Product",
      "category": "Accessories",
      "riskScore": 4.2
    }
  ]
}
```

Common errors:

- `products_unavailable`

### GET /api/products/{product_id}

Purpose: return the complete product detail payload.

Query params:

- `dateRange`: `30d`, `90d`, `365d`
- `region`: optional string
- `channel`: optional string

Consumed by:

- `Product Detail`

Response shape:

```json
{
  "product": {
    "id": 101,
    "sku": "SKU-101",
    "name": "Example Product",
    "category": "Accessories",
    "brand": "ChainWatch Demo"
  },
  "demand": {
    "demandRiskScore": 4.0,
    "historicalTrend": [],
    "seasonalWindows": [],
    "recentSpikes": []
  },
  "inventory": {
    "currentOnHand": 120,
    "reservedQty": 40,
    "inboundQty": 60,
    "daysOfCover": 8.5,
    "stockoutRiskScore": 4.3,
    "recommendedAction": "Replenish within 3 days"
  },
  "fulfillment": {
    "fulfillmentRiskScore": 3.8,
    "backlogOrders": 55,
    "avgShipDelayHours": 18,
    "onTimeRate": 0.87
  },
  "suppliers": [],
  "linkedRiskEvents": [],
  "lastUpdatedAt": "2026-04-23T12:00:00Z",
  "freshness": {
    "dataSource": "fresh",
    "lastUpdatedAt": "2026-04-23T12:00:00Z",
    "cacheUpdatedAt": "2026-04-23T12:00:00Z",
    "isStale": false,
    "refreshScheduled": false
  }
}
```

Common errors:

- `product_not_found`
- `product_detail_unavailable`

## Reports

### GET /api/reports

Purpose: return report list data for the Reports page.

Query params:

- `scopeType`: optional
- `status`: optional
- `limit`: optional integer

Consumed by:

- `Reports`

Response shape:

```json
{
  "items": [
    {
      "id": "rep_001",
      "title": "Weekly dashboard risk summary",
      "scopeType": "dashboard",
      "status": "completed",
      "createdAt": "2026-04-23T09:00:00Z",
      "markdownPath": "data/reports/markdown/rep_001.md"
    }
  ]
}
```

Common errors:

- `reports_unavailable`

### GET /api/reports/{report_id}

Purpose: return report metadata and preview content.

Consumed by:

- `Reports`

Response shape:

```json
{
  "id": "rep_001",
  "title": "Weekly dashboard risk summary",
  "scopeType": "dashboard",
  "scopeId": null,
  "status": "completed",
  "summary": "High inventory pressure across 8 SKUs.",
  "jsonPath": "data/reports/json/rep_001.json",
  "markdownPath": "data/reports/markdown/rep_001.md",
  "markdownPreview": "# Weekly dashboard risk summary\n...",
  "createdAt": "2026-04-23T09:00:00Z",
  "completedAt": "2026-04-23T09:00:03Z",
  "freshness": {
    "dataSource": "generated",
    "lastUpdatedAt": "2026-04-23T09:00:03Z",
    "cacheUpdatedAt": null,
    "isStale": false,
    "refreshScheduled": false
  }
}
```

Common errors:

- `report_not_found`

### POST /api/reports/generate

Purpose: enqueue or start generation of a new report.

Consumed by:

- `Reports`
- `Product Detail`
- `Map`

Request shape:

```json
{
  "scopeType": "product",
  "scopeId": "101",
  "reportType": "product_risk",
  "title": "Optional custom title"
}
```

Response shape:

```json
{
  "id": "rep_010",
  "status": "queued",
  "scopeType": "product",
  "scopeId": "101",
  "createdAt": "2026-04-23T12:05:00Z"
}
```

Common errors:

- `invalid_report_scope`
- `report_generation_failed`

## Imports

### GET /api/imports

Purpose: return recent import runs and statuses.

Consumed by:

- `Data Import/Settings`

Response shape:

```json
{
  "items": [
    {
      "id": "imp_001",
      "importType": "sales",
      "filename": "sales_history.csv",
      "status": "completed",
      "rowCount": 1825,
      "insertedCount": 1825,
      "errorCount": 0,
      "completedAt": "2026-04-23T11:00:00Z"
    }
  ]
}
```

Common errors:

- `imports_unavailable`

### POST /api/imports/products

Purpose: import product catalog CSV data.

Consumed by:

- `Data Import/Settings`

Request shape:

- multipart file upload or a local file reference handled by the backend import service

Response shape:

```json
{
  "id": "imp_010",
  "importType": "products",
  "status": "processing"
}
```

Common errors:

- `invalid_import_file`
- `product_import_failed`

### POST /api/imports/sales

Purpose: import historical sales CSV data.

Consumed by:

- `Data Import/Settings`

Request shape:

- multipart file upload or a local file reference handled by the backend import service

Response shape:

```json
{
  "id": "imp_011",
  "importType": "sales",
  "status": "processing"
}
```

Common errors:

- `invalid_import_file`
- `sales_import_failed`

### POST /api/imports/inventory

Purpose: import inventory snapshot CSV data.

Consumed by:

- `Data Import/Settings`

Request shape:

- multipart file upload or a local file reference handled by the backend import service

Response shape:

```json
{
  "id": "imp_012",
  "importType": "inventory",
  "status": "processing"
}
```

Common errors:

- `invalid_import_file`
- `inventory_import_failed`

### POST /api/imports/suppliers

Purpose: import supplier CSV data.

Consumed by:

- `Data Import/Settings`

Request shape:

- multipart file upload or a local file reference handled by the backend import service

Response shape:

```json
{
  "id": "imp_013",
  "importType": "suppliers",
  "status": "processing"
}
```

Common errors:

- `invalid_import_file`
- `supplier_import_failed`

## Consistency Requirements

- `Dashboard` must only rely on `GET /api/dashboard/summary` and `GET /api/dashboard/alerts`.
- `Map` must render from `GET /api/map/countries` and drill into `GET /api/map/countries/{country_code}`.
- `Product Detail` must be fully driven by `GET /api/products/{product_id}`.
- `Chat` must preserve `citations` and `usedAgents` from the backend response.
- `Reports` must expose both JSON and Markdown artifact paths.
