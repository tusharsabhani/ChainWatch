from __future__ import annotations

from app.schemas.common import CamelModel, FreshnessInfo


class ProductListItem(CamelModel):
    product_id: int
    sku: str
    name: str
    category: str
    risk_score: float


class ProductListResponse(CamelModel):
    items: list[ProductListItem]


class ProductHeader(CamelModel):
    id: int
    sku: str
    name: str
    category: str
    brand: str | None = None


class ProductDemandSection(CamelModel):
    demand_risk_score: float
    historical_trend: list[dict[str, object]]
    seasonal_windows: list[dict[str, object]]
    recent_spikes: list[dict[str, object]]


class ProductInventorySection(CamelModel):
    current_on_hand: int
    reserved_qty: int
    inbound_qty: int
    days_of_cover: float | None = None
    stockout_risk_score: float
    recommended_action: str


class ProductFulfillmentSection(CamelModel):
    fulfillment_risk_score: float
    backlog_orders: int
    avg_ship_delay_hours: float
    on_time_rate: float


class ProductSupplierItem(CamelModel):
    supplier_id: int
    supplier_code: str
    name: str
    country_code: str
    region: str | None = None
    lead_time_days: int | None = None
    reliability_score: float | None = None


class ProductLinkedRiskEvent(CamelModel):
    event_id: str
    title: str
    risk_type: str
    severity: int
    country_code: str | None = None
    source_url: str | None = None


class ProductDetailResponse(CamelModel):
    product: ProductHeader
    demand: ProductDemandSection
    inventory: ProductInventorySection
    fulfillment: ProductFulfillmentSection
    suppliers: list[ProductSupplierItem]
    linked_risk_events: list[ProductLinkedRiskEvent]
    last_updated_at: str | None = None
    freshness: FreshnessInfo | None = None
