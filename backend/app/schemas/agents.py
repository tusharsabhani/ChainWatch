from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AgentRunStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class AgentTriggerType(StrEnum):
    DASHBOARD = "dashboard"
    CHAT = "chat"
    MAP = "map"
    PRODUCT = "product"
    REPORT = "report"
    REFRESH = "refresh"


class Citation(BaseModel):
    title: str
    url: str
    source_name: str
    snippet: str | None = None


class AffectedSupplierRef(BaseModel):
    supplier_id: int
    supplier_code: str
    name: str
    country_code: str


class AffectedProductRef(BaseModel):
    product_id: int
    sku: str
    name: str
    category: str


class ExternalRiskAgentInput(BaseModel):
    country_codes: list[str] = Field(default_factory=list)
    supplier_countries: list[str] = Field(default_factory=list)
    route_hints: list[str] = Field(default_factory=list)
    product_category: str | None = None
    freshness_policy_hours: int = 6
    trigger_type: AgentTriggerType = AgentTriggerType.REFRESH
    trigger_ref: str | None = None


class ExternalRiskEvent(BaseModel):
    event_id: str
    source_type: str
    risk_type: str
    severity: int
    title: str
    summary: str
    country_code: str | None = None
    route_code: str | None = None
    affected_supplier_id: int | None = None
    affected_product_id: int | None = None
    event_date: str | None = None
    detected_at: str
    expires_at: str | None = None
    status: str
    source_url: str | None = None
    source_name: str | None = None
    citation_snippet: str | None = None
    confidence: float | None = None
    payload_json: str | None = None


class CountryRiskScore(BaseModel):
    country_code: str
    score_date: str
    overall_score: float
    geopolitical_score: float
    tariff_score: float
    logistics_score: float
    weather_score: float
    labor_score: float
    active_event_count: int
    highest_severity: int
    summary: str | None = None


class ExternalRiskAgentOutput(BaseModel):
    risk_events: list[ExternalRiskEvent]
    country_scores: list[CountryRiskScore]
    citations: list[Citation]
    summary: str
    highest_severity: int
    affected_suppliers: list[AffectedSupplierRef]
    affected_products: list[AffectedProductRef]
    limitations: list[str] = Field(default_factory=list)
    data_source: str = "empty"


class DemandAgentInput(BaseModel):
    product_ids: list[int]
    region_filter: str | None = None
    channel_filter: str | None = None
    forecast_window_days: int = 30
    trigger_type: AgentTriggerType = AgentTriggerType.PRODUCT
    trigger_ref: str | None = None


class HistoricalTrendPoint(BaseModel):
    period_start: str
    units_sold: int
    net_revenue: float
    returns_qty: int
    promo_periods: int
    stockout_periods: int


class SeasonalWindow(BaseModel):
    start_month: int
    end_month: int
    avg_units: float
    label: str


class RecentSpike(BaseModel):
    period_start: str
    units_sold: int
    baseline_units: float
    spike_ratio: float
    reason: str


class DemandAgentOutput(BaseModel):
    historical_trend: list[HistoricalTrendPoint]
    seasonal_windows: list[SeasonalWindow]
    recent_spikes: list[RecentSpike]
    forecast_window_days: int
    forecasted_units: int
    demand_risk_score: float
    supporting_notes: list[str] = Field(default_factory=list)
    low_confidence: bool = False


class DemandSignal(BaseModel):
    product_id: int
    forecast_window_days: int
    forecasted_units: int
    demand_risk_score: float


class InventoryAgentInput(BaseModel):
    product_ids: list[int]
    demand_signals: list[DemandSignal] = Field(default_factory=list)
    trigger_type: AgentTriggerType = AgentTriggerType.PRODUCT
    trigger_ref: str | None = None


class InventoryAgentOutput(BaseModel):
    current_on_hand: int
    reserved_qty: int
    inbound_qty: int
    days_of_cover: float | None = None
    reorder_point: int
    stockout_risk_score: float
    inventory_status: str
    recommended_action: str
    supporting_notes: list[str] = Field(default_factory=list)
    partial: bool = False


class FulfillmentRegionStatus(BaseModel):
    region_code: str
    backlog_orders: int
    avg_ship_delay_hours: float
    on_time_rate: float
    sla_risk_level: int
    warehouse_count: int


class FulfillmentAgentInput(BaseModel):
    product_ids: list[int] = Field(default_factory=list)
    region_codes: list[str] = Field(default_factory=list)
    external_risk_events: list[ExternalRiskEvent] = Field(default_factory=list)
    trigger_type: AgentTriggerType = AgentTriggerType.PRODUCT
    trigger_ref: str | None = None


class FulfillmentAgentOutput(BaseModel):
    regional_status: list[FulfillmentRegionStatus]
    backlog_orders: int
    avg_ship_delay_hours: float
    on_time_rate: float
    fulfillment_risk_score: float
    sla_risk_level: int
    recommended_action: str
    supporting_notes: list[str] = Field(default_factory=list)
    partial: bool = False
