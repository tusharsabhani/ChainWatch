# PRD

## Product Name

`ChainWatch`

## Product Summary

ChainWatch is a local-first retail operations product that helps teams understand inventory risk, fulfillment risk, and external market disruptions in one place. It combines internal retail data with live external-risk monitoring to help operators decide what to escalate, replenish, reroute, or watch more closely.

## Product Vision

Give retail operations teams a single operational surface where they can understand:

- what is at risk,
- why it is at risk,
- which products, suppliers, and countries are involved,
- and what action should be taken next.

## Target Users

### Primary users

- `Inventory Planner`
  - Needs early warning on stockout pressure and reorder urgency.
- `E-commerce Operations Manager`
  - Needs visibility into fulfillment delays and customer-impacting risk.
- `Category Manager`
  - Needs to understand supplier and region-level exposure across product lines.

### Secondary users

- `Retail Analyst`
  - Needs structured reports and traceable risk evidence.
- `Operations Leadership`
  - Needs a high-level dashboard and shareable risk summaries.

## Core User Jobs To Be Done

- Help me see which products are most at risk right now.
- Help me understand whether the risk is driven by demand, stock, fulfillment, or external events.
- Help me trace a risk to a supplier, route, or country.
- Help me ask natural-language questions and get grounded answers with sources.
- Help me generate a report I can share with stakeholders.
- Help me import and review local data without standing up cloud infrastructure.

## Problem Definition

Retail operations data is fragmented across spreadsheets, dashboards, supplier updates, and ad hoc news monitoring. Teams often know that an issue exists only after it shows up as a missed SLA, a stockout, or a reactive escalation. They need a product that ties together:

- `historical demand patterns`
- `current inventory position`
- `fulfillment performance`
- `external disruption signals`

without forcing them to build a full enterprise platform before learning whether the workflow is useful.

## In Scope For MVP

- Local-first application architecture
- Historical sales analysis using `3-5 years` of sales data
- Inventory and reorder risk analysis
- Fulfillment delay and SLA risk monitoring
- External country and route risk tracking through a search-backed agent
- Dashboard view of KPIs, alerts, trends, and top-risk entities
- Chat interface with grounded answers and citations
- Country-level map highlighting active issues
- Product detail drilldown for a single SKU
- Local report generation in JSON and Markdown
- CSV import flow for products, suppliers, inventory, and sales data

## Out Of Scope For MVP

- Automated purchasing or supplier communication
- Multi-user auth and permissions
- Cloud storage and managed databases
- Real-time streaming ingestion
- Mobile app support
- ERP write-back
- Financial planning and budgeting workflows
- Native PDF export

## Product Principles

- `Actionable`: every major surface should help the user decide what to do next.
- `Traceable`: every major risk claim should be explainable.
- `Local-first`: the product must run from the project directory.
- `Composable`: pages should share the same backend data contracts.
- `Provider-agnostic`: LLM and search integrations should stay abstract.

## Feature Definitions

### Dashboard

Show operational KPIs, active alerts, top at-risk products, top at-risk suppliers, and recent trend lines.

### Chat

Answer questions about products, suppliers, countries, fulfillment performance, and external disruptions using coordinated backend agents with citations.

### Map

Render a world view of country-level external risk so operators can click into affected countries and understand which suppliers and SKUs are exposed.

### Reports

Generate, browse, and inspect local risk reports in JSON and Markdown format.

### Product Detail

Provide a single-SKU view that combines demand trend, stock position, supplier exposure, fulfillment health, and linked risk events.

### Data Import/Settings

Let the user import local CSV files and confirm that the application is ready to use with the expected providers and storage paths.

## Success Criteria

The MVP is successful when:

- A user can import local sample data and browse it through the dashboard and product views.
- A user can ask a grounded question in chat and receive a cited answer.
- A country-level risk event appears on the map and influences downstream views.
- A user can generate and open a structured report for a product, country, or dashboard scope.
- The docs and codebase can be extended later without changing the fundamental stack.

## Non-Goals

- Do not optimize for enterprise-scale throughput in v1.
- Do not attempt full BI coverage.
- Do not build a generic agent playground.
- Do not reproduce procurement risk tooling.

## MVP Boundaries

- One local project instance
- One sqlite database
- One local filesystem artifact store
- One configured LLM provider adapter
- One configured search provider adapter
- One primary retail sample dataset for development

## Dependencies

- Local CSV or seeded sample data
- LLM API key, to be selected later
- Web-search API key, to be selected later

## Risks

- External-risk search results may vary by provider and freshness.
- Retail sample data may need normalization before analysis is meaningful.
- Agent outputs may be noisy if sales history is sparse or external citations are weak.

These risks are acceptable for the MVP and should be managed through explicit caching, transparent agent outputs, and strong report structure.
