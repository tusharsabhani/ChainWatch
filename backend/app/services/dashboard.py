from __future__ import annotations

from datetime import datetime, timezone

from app.adapters.search import NullSearchAdapter, SearchAdapter
from app.agents.demand import DemandAgent
from app.agents.external_risk import ExternalRiskAgent
from app.agents.fulfillment import FulfillmentAgent
from app.config import Settings
from app.db.connection import SQLiteConnectionFactory
from app.db.repositories.catalog_repository import CatalogRepository
from app.schemas.agents import AgentTriggerType, DemandAgentInput, ExternalRiskAgentInput, FulfillmentAgentInput
from app.schemas.dashboard import (
    DashboardAlertItem,
    DashboardAlertsResponse,
    DashboardCountryExposure,
    DashboardFilters,
    DashboardKpis,
    DashboardSummaryResponse,
    DashboardTopRiskProduct,
    DashboardTopRiskSupplier,
    DashboardTrendPoint,
    DashboardTrendSet,
)
from app.services.products import ProductService
from app.services.storage import StorageManager


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DashboardService:
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
        self.search_adapter = search_adapter or NullSearchAdapter()
        self.external_risk_agent = ExternalRiskAgent(
            settings=settings,
            storage=storage,
            database=database,
            search_adapter=self.search_adapter,
        )
        self.demand_agent = DemandAgent(
            settings=settings,
            storage=storage,
            database=database,
        )
        self.fulfillment_agent = FulfillmentAgent(
            settings=settings,
            storage=storage,
            database=database,
        )
        self.product_service = ProductService(
            settings=settings,
            storage=storage,
            database=database,
            search_adapter=self.search_adapter,
        )

    def get_summary(
        self,
        *,
        date_range: str = "30d",
        severity_min: int = 3,
        category: str | None = None,
        region: str | None = None,
    ) -> DashboardSummaryResponse:
        products = self.catalog_repository.search_products(
            category=category,
            limit=500,
        )
        product_snapshots = self.product_service.list_product_risk_snapshots(
            products=products,
            region=region,
        )

        country_codes = sorted(
            {
                country_code
                for product in products
                for country_code in self.catalog_repository.list_supplier_country_codes_for_product_ids([product.id])
            }
        )
        external_output = self.external_risk_agent.run(
            ExternalRiskAgentInput(
                country_codes=country_codes,
                freshness_policy_hours=self.settings.external_risk_cache_ttl_hours,
                trigger_type=AgentTriggerType.DASHBOARD,
                trigger_ref="dashboard-summary",
            )
        )
        filtered_country_scores = [
            score
            for score in external_output.country_scores
            if score.highest_severity >= severity_min
        ]
        exposed_country_codes = {score.country_code for score in filtered_country_scores}
        exposed_supplier_rows = [
            supplier
            for supplier in self.catalog_repository.list_suppliers_by_country_codes(list(exposed_country_codes))
        ]
        filtered_events = [
            event
            for event in external_output.risk_events
            if event.severity >= severity_min
        ]

        demand_trend_output = self.demand_agent.run(
            DemandAgentInput(
                product_ids=[product.id for product in products],
                region_filter=region,
                trigger_type=AgentTriggerType.DASHBOARD,
                trigger_ref="dashboard-trends",
            )
        ) if products else None
        fulfillment_output = self.fulfillment_agent.run(
            FulfillmentAgentInput(
                product_ids=[product.id for product in products],
                trigger_type=AgentTriggerType.DASHBOARD,
                trigger_ref="dashboard-trends",
                external_risk_events=external_output.risk_events,
            )
        ) if products else None

        last_updated_candidates = [
            event.detected_at
            for event in external_output.risk_events
        ]
        last_updated_at = max(last_updated_candidates) if last_updated_candidates else _utc_now_iso()

        return DashboardSummaryResponse(
            filters=DashboardFilters(
                date_range=date_range,
                severity_min=severity_min,
                category=category,
                region=region,
            ),
            kpis=DashboardKpis(
                active_alerts=len(filtered_events),
                products_at_risk=len([item for item in product_snapshots if item.risk_score >= severity_min]),
                suppliers_exposed=len(exposed_supplier_rows),
                countries_with_issues=len(filtered_country_scores),
            ),
            top_risk_products=[
                DashboardTopRiskProduct(
                    product_id=item.product_id,
                    sku=item.sku,
                    name=item.name,
                    risk_score=item.risk_score,
                    primary_risk_driver=item.primary_risk_driver,
                )
                for item in product_snapshots[:5]
            ],
            top_risk_suppliers=[
                DashboardTopRiskSupplier(
                    supplier_id=supplier.id,
                    name=supplier.name,
                    country_code=supplier.country_code,
                    risk_score=round(
                        next(
                            (
                                score.overall_score
                                for score in filtered_country_scores
                                if score.country_code == supplier.country_code
                            ),
                            1.0,
                        ),
                        2,
                    ),
                    active_issue_count=next(
                        (
                            score.active_event_count
                            for score in filtered_country_scores
                            if score.country_code == supplier.country_code
                        ),
                        0,
                    ),
                )
                for supplier in exposed_supplier_rows[:5]
            ],
            country_exposure=[
                DashboardCountryExposure(
                    country_code=score.country_code,
                    overall_score=round(score.overall_score, 2),
                    active_event_count=score.active_event_count,
                )
                for score in filtered_country_scores
            ],
            trends=DashboardTrendSet(
                demand_pressure=[
                    DashboardTrendPoint(
                        label=point.period_start,
                        value=float(point.units_sold),
                    )
                    for point in (demand_trend_output.historical_trend[-6:] if demand_trend_output else [])
                ],
                sla_risk=[
                    DashboardTrendPoint(
                        label=region_status.region_code,
                        value=float(region_status.sla_risk_level),
                    )
                    for region_status in (fulfillment_output.regional_status if fulfillment_output else [])
                ],
                external_event_count=[
                    DashboardTrendPoint(
                        label=score.country_code,
                        value=float(score.active_event_count),
                    )
                    for score in external_output.country_scores
                ],
            ),
            last_updated_at=last_updated_at,
        )

    def get_alerts(
        self,
        *,
        severity_min: int = 1,
        status: str | None = None,
        limit: int = 25,
    ) -> DashboardAlertsResponse:
        country_codes = self.catalog_repository.list_all_supplier_country_codes()
        external_output = self.external_risk_agent.run(
            ExternalRiskAgentInput(
                country_codes=country_codes,
                freshness_policy_hours=self.settings.external_risk_cache_ttl_hours,
                trigger_type=AgentTriggerType.DASHBOARD,
                trigger_ref="dashboard-alerts",
            )
        )
        events = [
            event
            for event in external_output.risk_events
            if event.severity >= severity_min and (status is None or event.status == status)
        ]
        events = sorted(events, key=lambda event: (-event.severity, event.detected_at))[:limit]
        last_updated_at = max((event.detected_at for event in events), default=_utc_now_iso())

        return DashboardAlertsResponse(
            items=[
                DashboardAlertItem(
                    event_id=event.event_id,
                    title=event.title,
                    risk_type=event.risk_type,
                    severity=event.severity,
                    country_code=event.country_code,
                    affected_supplier_id=event.affected_supplier_id,
                    affected_product_id=event.affected_product_id,
                    status=event.status,
                    detected_at=event.detected_at,
                )
                for event in events
            ],
            total=len(events),
            last_updated_at=last_updated_at,
        )
