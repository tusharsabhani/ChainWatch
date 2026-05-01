from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from fastapi import BackgroundTasks

from app.adapters.search import NullSearchAdapter, SearchAdapter
from app.agents.demand import DemandAgent
from app.agents.fulfillment import FulfillmentAgent
from app.agents.inventory import InventoryAgent
from app.config import Settings
from app.db.connection import SQLiteConnectionFactory
from app.db.repositories.catalog_repository import CatalogRepository
from app.schemas.agents import (
    AgentTriggerType,
    DemandAgentInput,
    DemandSignal,
    ExternalRiskAgentInput,
    FulfillmentAgentInput,
    InventoryAgentInput,
)
from app.schemas.catalog import ProductRecord
from app.schemas.products import (
    ProductDemandSection,
    ProductDetailResponse,
    ProductFulfillmentSection,
    ProductHeader,
    ProductInventorySection,
    ProductLinkedRiskEvent,
    ProductListItem,
    ProductListResponse,
    ProductSupplierItem,
)
from app.services.external_risk import ExternalRiskService
from app.services.storage import StorageManager


def _cutoff_for_date_range(date_range: str) -> date | None:
    mapping = {
        "30d": 30,
        "90d": 90,
        "365d": 365,
    }
    if date_range not in mapping:
        return None
    return datetime.now(timezone.utc).date() - timedelta(days=mapping[date_range])


@dataclass(slots=True)
class ProductRiskSnapshot:
    product_id: int
    sku: str
    name: str
    category: str
    risk_score: float
    primary_risk_driver: str


class ProductService:
    def __init__(
        self,
        *,
        settings: Settings,
        storage: StorageManager,
        database: SQLiteConnectionFactory,
        search_adapter: SearchAdapter | None = None,
    ) -> None:
        self.settings = settings
        self.storage = storage
        self.database = database
        self.catalog_repository = CatalogRepository(database)
        self.demand_agent = DemandAgent(
            settings=settings,
            storage=storage,
            database=database,
        )
        self.inventory_agent = InventoryAgent(
            settings=settings,
            storage=storage,
            database=database,
        )
        self.fulfillment_agent = FulfillmentAgent(
            settings=settings,
            storage=storage,
            database=database,
        )
        self.external_risk_service = ExternalRiskService(
            settings=settings,
            storage=storage,
            database=database,
            search_adapter=search_adapter or NullSearchAdapter(),
        )

    def list_products(
        self,
        *,
        query: str | None = None,
        category: str | None = None,
        risk_min: float | None = None,
        limit: int = 25,
        region: str | None = None,
        channel: str | None = None,
    ) -> ProductListResponse:
        products = self.catalog_repository.search_products(
            query=query,
            category=category,
            limit=limit,
        )
        snapshots = self.list_product_risk_snapshots(
            products=products,
            region=region,
            channel=channel,
        )
        if risk_min is not None:
            snapshots = [snapshot for snapshot in snapshots if snapshot.risk_score >= risk_min]
        return ProductListResponse(
            items=[
                ProductListItem(
                    product_id=snapshot.product_id,
                    sku=snapshot.sku,
                    name=snapshot.name,
                    category=snapshot.category,
                    risk_score=snapshot.risk_score,
                )
                for snapshot in snapshots
            ]
        )

    def list_product_risk_snapshots(
        self,
        *,
        products: list[ProductRecord] | None = None,
        region: str | None = None,
        channel: str | None = None,
    ) -> list[ProductRiskSnapshot]:
        target_products = products or self.catalog_repository.list_all_products()

        all_country_codes = sorted(
            {
                country_code
                for product in target_products
                for country_code in self.catalog_repository.list_supplier_country_codes_for_product_ids([product.id])
            }
        )
        external_envelope = self.external_risk_service.load(
            ExternalRiskAgentInput(
                country_codes=all_country_codes,
                freshness_policy_hours=self.settings.external_risk_cache_ttl_hours,
                trigger_type=AgentTriggerType.DASHBOARD,
                trigger_ref="products-list",
            ),
            prefer_cached=True,
        )
        external_output = external_envelope.output
        country_score_map = {
            score.country_code: score.overall_score
            for score in external_output.country_scores
        }

        snapshots = [
            self._build_risk_snapshot(
                product=product,
                region=region,
                channel=channel,
                country_score_map=country_score_map,
            )
            for product in target_products
        ]
        return sorted(snapshots, key=lambda item: item.risk_score, reverse=True)

    def get_product_detail(
        self,
        *,
        product_id: int,
        date_range: str = "90d",
        region: str | None = None,
        channel: str | None = None,
        background_tasks: BackgroundTasks | None = None,
    ) -> ProductDetailResponse:
        product = self.catalog_repository.get_product_by_id(product_id)
        if product is None:
            raise LookupError(f"Product {product_id} was not found.")

        suppliers = self.catalog_repository.list_product_suppliers(product_id)
        supplier_country_codes = sorted({supplier.country_code for supplier in suppliers if supplier.country_code})

        demand_output = self.demand_agent.run(
            DemandAgentInput(
                product_ids=[product_id],
                region_filter=region,
                channel_filter=channel,
                trigger_type=AgentTriggerType.PRODUCT,
                trigger_ref=str(product_id),
            )
        )
        cutoff = _cutoff_for_date_range(date_range)
        historical_trend = demand_output.historical_trend
        if cutoff is not None:
            historical_trend = [
                point
                for point in historical_trend
                if date.fromisoformat(point.period_start) >= cutoff
            ]

        demand_signal = [
            DemandSignal(
                product_id=product_id,
                forecast_window_days=demand_output.forecast_window_days,
                forecasted_units=demand_output.forecasted_units,
                demand_risk_score=demand_output.demand_risk_score,
            )
        ]
        inventory_output = self.inventory_agent.run(
            InventoryAgentInput(
                product_ids=[product_id],
                demand_signals=demand_signal,
                trigger_type=AgentTriggerType.PRODUCT,
                trigger_ref=str(product_id),
            )
        )
        external_envelope = self.external_risk_service.load(
            ExternalRiskAgentInput(
                country_codes=supplier_country_codes,
                freshness_policy_hours=self.settings.external_risk_cache_ttl_hours,
                trigger_type=AgentTriggerType.PRODUCT,
                trigger_ref=str(product_id),
            ),
            background_tasks=background_tasks,
            prefer_cached=True,
        )
        external_output = external_envelope.output
        fulfillment_output = self.fulfillment_agent.run(
            FulfillmentAgentInput(
                product_ids=[product_id],
                external_risk_events=external_output.risk_events,
                trigger_type=AgentTriggerType.PRODUCT,
                trigger_ref=str(product_id),
            )
        )

        return ProductDetailResponse(
            product=ProductHeader(
                id=product.id,
                sku=product.sku,
                name=product.name,
                category=product.category,
                brand=product.brand,
            ),
            demand=ProductDemandSection(
                demand_risk_score=demand_output.demand_risk_score,
                historical_trend=[point.model_dump(mode="json") for point in historical_trend],
                seasonal_windows=[window.model_dump(mode="json") for window in demand_output.seasonal_windows],
                recent_spikes=[spike.model_dump(mode="json") for spike in demand_output.recent_spikes],
            ),
            inventory=ProductInventorySection(
                current_on_hand=inventory_output.current_on_hand,
                reserved_qty=inventory_output.reserved_qty,
                inbound_qty=inventory_output.inbound_qty,
                days_of_cover=inventory_output.days_of_cover,
                stockout_risk_score=inventory_output.stockout_risk_score,
                recommended_action=inventory_output.recommended_action,
            ),
            fulfillment=ProductFulfillmentSection(
                fulfillment_risk_score=fulfillment_output.fulfillment_risk_score,
                backlog_orders=fulfillment_output.backlog_orders,
                avg_ship_delay_hours=fulfillment_output.avg_ship_delay_hours,
                on_time_rate=fulfillment_output.on_time_rate,
            ),
            suppliers=[
                ProductSupplierItem(
                    supplier_id=supplier.id,
                    supplier_code=supplier.supplier_code,
                    name=supplier.name,
                    country_code=supplier.country_code,
                    region=supplier.region,
                    lead_time_days=supplier.lead_time_days,
                    reliability_score=supplier.reliability_score,
                )
                for supplier in suppliers
            ],
            linked_risk_events=[
                ProductLinkedRiskEvent(
                    event_id=event.event_id,
                    title=event.title,
                    risk_type=event.risk_type,
                    severity=event.severity,
                    country_code=event.country_code,
                    source_url=event.source_url,
                )
                for event in external_output.risk_events
            ],
            last_updated_at=external_envelope.freshness.last_updated_at,
            freshness=external_envelope.freshness,
        )

    def _build_risk_snapshot(
        self,
        *,
        product: ProductRecord,
        region: str | None,
        channel: str | None,
        country_score_map: dict[str, float],
    ) -> ProductRiskSnapshot:
        demand_output = self.demand_agent.run(
            DemandAgentInput(
                product_ids=[product.id],
                region_filter=region,
                channel_filter=channel,
                trigger_type=AgentTriggerType.DASHBOARD,
                trigger_ref=f"product-{product.id}",
            )
        )
        inventory_output = self.inventory_agent.run(
            InventoryAgentInput(
                product_ids=[product.id],
                demand_signals=[
                    DemandSignal(
                        product_id=product.id,
                        forecast_window_days=demand_output.forecast_window_days,
                        forecasted_units=demand_output.forecasted_units,
                        demand_risk_score=demand_output.demand_risk_score,
                    )
                ],
                trigger_type=AgentTriggerType.DASHBOARD,
                trigger_ref=f"product-{product.id}",
            )
        )
        fulfillment_output = self.fulfillment_agent.run(
            FulfillmentAgentInput(
                product_ids=[product.id],
                trigger_type=AgentTriggerType.DASHBOARD,
                trigger_ref=f"product-{product.id}",
            )
        )
        supplier_country_codes = self.catalog_repository.list_supplier_country_codes_for_product_ids([product.id])
        external_score = max(
            (country_score_map.get(country_code, 1.0) for country_code in supplier_country_codes),
            default=1.0,
        )

        components = {
            "demand": demand_output.demand_risk_score,
            "inventory": inventory_output.stockout_risk_score,
            "fulfillment": fulfillment_output.fulfillment_risk_score,
            "external": external_score,
        }
        primary_risk_driver, risk_score = max(
            components.items(),
            key=lambda item: item[1],
        )
        return ProductRiskSnapshot(
            product_id=product.id,
            sku=product.sku,
            name=product.name,
            category=product.category,
            risk_score=round(float(risk_score), 2),
            primary_risk_driver=primary_risk_driver,
        )
