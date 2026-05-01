from __future__ import annotations

from datetime import datetime, timezone

from fastapi import BackgroundTasks

from app.adapters.search import NullSearchAdapter, SearchAdapter
from app.config import Settings
from app.db.connection import SQLiteConnectionFactory
from app.db.repositories.catalog_repository import CatalogRepository
from app.schemas.agents import AgentTriggerType, ExternalRiskAgentInput
from app.schemas.map import (
    CountryDetailResponse,
    CountryDetailSummary,
    CountryIssueItem,
    CountryProductRef,
    CountrySupplierRef,
    MapCountriesResponse,
    MapCountrySummaryItem,
)
from app.services.countries import country_name
from app.services.external_risk import ExternalRiskService
from app.services.storage import StorageManager


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MapService:
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
        self.external_risk_service = ExternalRiskService(
            settings=settings,
            storage=storage,
            database=database,
            search_adapter=search_adapter or NullSearchAdapter(),
        )

    def list_countries(
        self,
        *,
        risk_type: str | None = None,
        severity_min: int = 1,
        background_tasks: BackgroundTasks | None = None,
    ) -> MapCountriesResponse:
        country_codes = self.catalog_repository.list_all_supplier_country_codes()
        envelope = self.external_risk_service.load(
            ExternalRiskAgentInput(
                country_codes=country_codes,
                freshness_policy_hours=self.settings.external_risk_cache_ttl_hours,
                trigger_type=AgentTriggerType.MAP,
                trigger_ref="map-countries",
            ),
            background_tasks=background_tasks,
            prefer_cached=True,
        )
        output = envelope.output

        items: list[MapCountrySummaryItem] = []
        for score in output.country_scores:
            related_events = [
                event
                for event in output.risk_events
                if event.country_code == score.country_code
                and event.severity >= severity_min
                and (risk_type is None or event.risk_type == risk_type)
            ]
            if risk_type and not related_events:
                continue
            if not risk_type and score.highest_severity < severity_min:
                continue

            active_event_count = len(related_events) if risk_type else score.active_event_count
            highest_severity = max((event.severity for event in related_events), default=score.highest_severity)
            overall_score = (
                round(sum(event.severity for event in related_events) / len(related_events), 2)
                if related_events
                else round(score.overall_score, 2)
            )
            items.append(
                MapCountrySummaryItem(
                    country_code=score.country_code,
                    country_name=country_name(score.country_code),
                    overall_score=overall_score,
                    highest_severity=highest_severity,
                    active_event_count=active_event_count,
                )
            )

        last_updated_at = envelope.freshness.last_updated_at or _utc_now_iso()
        return MapCountriesResponse(
            items=sorted(items, key=lambda item: (-item.overall_score, item.country_code)),
            last_updated_at=last_updated_at,
            freshness=envelope.freshness,
        )

    def get_country_detail(
        self,
        country_code: str,
        *,
        background_tasks: BackgroundTasks | None = None,
    ) -> CountryDetailResponse:
        normalized_code = country_code.strip().upper()
        envelope = self.external_risk_service.load(
            ExternalRiskAgentInput(
                country_codes=[normalized_code],
                freshness_policy_hours=self.settings.external_risk_cache_ttl_hours,
                trigger_type=AgentTriggerType.MAP,
                trigger_ref=normalized_code,
            ),
            background_tasks=background_tasks,
            prefer_cached=True,
        )
        output = envelope.output
        known_countries = set(self.catalog_repository.list_all_supplier_country_codes())
        if normalized_code not in known_countries and not output.country_scores and not output.risk_events:
            raise LookupError(f"Country {normalized_code} was not found.")

        country_score = next(
            (score for score in output.country_scores if score.country_code == normalized_code),
            None,
        )
        summary = (
            country_score.summary
            if country_score and country_score.summary
            else "No active external issues are currently surfaced for this country."
        )
        overall_score = round(country_score.overall_score, 2) if country_score else 1.0

        return CountryDetailResponse(
            country=CountryDetailSummary(
                country_code=normalized_code,
                country_name=country_name(normalized_code),
                overall_score=overall_score,
                summary=summary,
            ),
            issues=[
                CountryIssueItem(
                    event_id=event.event_id,
                    title=event.title,
                    risk_type=event.risk_type,
                    severity=event.severity,
                    source_url=event.source_url,
                )
                for event in output.risk_events
                if event.country_code == normalized_code
            ],
            affected_suppliers=[
                CountrySupplierRef(
                    supplier_id=supplier.supplier_id,
                    name=supplier.name,
                )
                for supplier in output.affected_suppliers
                if supplier.country_code == normalized_code
            ],
            affected_products=[
                CountryProductRef(
                    product_id=product.product_id,
                    sku=product.sku,
                    name=product.name,
                )
                for product in output.affected_products
            ],
            last_updated_at=envelope.freshness.last_updated_at,
            freshness=envelope.freshness,
        )
