from __future__ import annotations

from app.schemas.common import CamelModel


class DashboardFilters(CamelModel):
    date_range: str
    severity_min: int
    category: str | None = None
    region: str | None = None


class DashboardKpis(CamelModel):
    active_alerts: int
    products_at_risk: int
    suppliers_exposed: int
    countries_with_issues: int


class DashboardTopRiskProduct(CamelModel):
    product_id: int
    sku: str
    name: str
    risk_score: float
    primary_risk_driver: str


class DashboardTopRiskSupplier(CamelModel):
    supplier_id: int
    name: str
    country_code: str
    risk_score: float
    active_issue_count: int


class DashboardCountryExposure(CamelModel):
    country_code: str
    overall_score: float
    active_event_count: int


class DashboardTrendPoint(CamelModel):
    label: str
    value: float


class DashboardTrendSet(CamelModel):
    demand_pressure: list[DashboardTrendPoint]
    sla_risk: list[DashboardTrendPoint]
    external_event_count: list[DashboardTrendPoint]


class DashboardSummaryResponse(CamelModel):
    filters: DashboardFilters
    kpis: DashboardKpis
    top_risk_products: list[DashboardTopRiskProduct]
    top_risk_suppliers: list[DashboardTopRiskSupplier]
    country_exposure: list[DashboardCountryExposure]
    trends: DashboardTrendSet
    last_updated_at: str


class DashboardAlertItem(CamelModel):
    event_id: str
    title: str
    risk_type: str
    severity: int
    country_code: str | None = None
    affected_supplier_id: int | None = None
    affected_product_id: int | None = None
    status: str
    detected_at: str


class DashboardAlertsResponse(CamelModel):
    items: list[DashboardAlertItem]
    total: int
    last_updated_at: str
