from __future__ import annotations

from app.schemas.common import CamelModel, FreshnessInfo


class MapCountrySummaryItem(CamelModel):
    country_code: str
    country_name: str
    overall_score: float
    highest_severity: int
    active_event_count: int


class MapCountriesResponse(CamelModel):
    items: list[MapCountrySummaryItem]
    last_updated_at: str
    freshness: FreshnessInfo | None = None


class CountryDetailSummary(CamelModel):
    country_code: str
    country_name: str
    overall_score: float
    summary: str


class CountryIssueItem(CamelModel):
    event_id: str
    title: str
    risk_type: str
    severity: int
    source_url: str | None = None


class CountrySupplierRef(CamelModel):
    supplier_id: int
    name: str


class CountryProductRef(CamelModel):
    product_id: int
    sku: str
    name: str


class CountryDetailResponse(CamelModel):
    country: CountryDetailSummary
    issues: list[CountryIssueItem]
    affected_suppliers: list[CountrySupplierRef]
    affected_products: list[CountryProductRef]
    last_updated_at: str | None = None
    freshness: FreshnessInfo | None = None
