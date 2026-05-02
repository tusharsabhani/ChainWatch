from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from app.adapters.search import NullSearchAdapter
from app.agents.external_risk import ExternalRiskAgent
from app.config import Settings
from app.db.connection import SQLiteConnectionFactory
from app.db.repositories.catalog_repository import CatalogRepository
from app.db.repositories.risk_repository import RiskRepository
from app.schemas.agents import (
    AffectedProductRef,
    AffectedSupplierRef,
    Citation,
    ExternalRiskAgentInput,
    ExternalRiskAgentOutput,
    ExternalRiskEvent,
)
from app.services.citations import dedupe_citations
from app.services.countries import country_name, map_watchlist_country_codes
from app.services.storage import StorageManager

SNAPSHOT_DETECTED_AT = "2026-05-02T12:00:00+00:00"
SNAPSHOT_SUMMARY_NOTE = (
    "Curated local external-risk snapshot stored on May 2, 2026. "
    "Live search refresh is disabled for this snapshot."
)

MANUAL_RISK_ITEMS = (
    {
        "country_code": "IR",
        "risk_type": "geopolitical",
        "severity": 5,
        "title": "Hormuz shipping traffic remains at a trickle as U.S.-Iran deadlock deepens",
        "summary": "Reuters reported on April 29, 2026 that only a small fraction of normal vessel traffic was moving through the Strait of Hormuz while negotiations remained stalled.",
        "event_date": "2026-04-29",
        "route_code": "HORMUZ",
        "source_url": "https://www.internazionale.it/ultime-notizie-reuters/2026/04/29/hormuz-shipping-traffic-remains-at-a-trickle-as-us-iran-deadlock-deepens",
        "source_name": "Reuters / Internazionale",
        "citation_snippet": "Traffic through the Strait of Hormuz remained a fraction of normal flows.",
    },
    {
        "country_code": "OM",
        "risk_type": "logistics",
        "severity": 5,
        "title": "Only five ships pass through the Strait of Hormuz in 24 hours",
        "summary": "Reuters reported on April 24, 2026 that ship transits through the waterway near Oman were still far below the normal daily passage count, signaling a severe logistics disruption.",
        "event_date": "2026-04-24",
        "route_code": "HORMUZ",
        "source_url": "https://www.internazionale.it/ultime-notizie-reuters/2026/04/24/only-five-ships-pass-through-strait-of-hormuz-in-24-hours",
        "source_name": "Reuters / Internazionale",
        "citation_snippet": "Only five ships passed through the waterway in 24 hours.",
    },
    {
        "country_code": "AE",
        "risk_type": "logistics",
        "severity": 5,
        "title": "Gulf shipping crisis deepens with tankers stranded off Fujairah",
        "summary": "Reuters reported on March 4, 2026 that the war-driven Hormuz disruption had stranded tankers near Fujairah in the United Arab Emirates and choked off key regional flows.",
        "event_date": "2026-03-04",
        "route_code": "HORMUZ",
        "source_url": "https://www.investing.com/news/commodities-news/hormuz-shutdown-worsens-after-us-hits-iranian-warship-tankers-stranded-for-fifth-day-4541147",
        "source_name": "Reuters / Investing.com",
        "citation_snippet": "Tankers were stranded near Fujairah as the crisis deepened.",
    },
    {
        "country_code": "SA",
        "risk_type": "geopolitical",
        "severity": 5,
        "title": "Iran attacks Saudi Arabia's Jubail petrochemical complex",
        "summary": "Reuters reported on April 8, 2026 that the Jubail petrochemical complex was attacked, raising industrial and export disruption risk across Saudi Arabia.",
        "event_date": "2026-04-08",
        "route_code": None,
        "source_url": "https://www.gmanetwork.com/news/topstories/world/982995/iran-has-attacked-saudi-arabia-s-jubail-petrochemical-complex-irgc-says/story/",
        "source_name": "Reuters / GMA News",
        "citation_snippet": "The attack hit a core downstream energy complex in Saudi Arabia.",
    },
    {
        "country_code": "KR",
        "risk_type": "labor",
        "severity": 4,
        "title": "Samsung asks court to block illegal strike activities by unions",
        "summary": "Reuters reported on April 16, 2026 that Samsung's wage dispute in South Korea was escalating toward strike action with potential semiconductor output disruption.",
        "event_date": "2026-04-16",
        "route_code": None,
        "source_url": "https://www.investing.com/news/stock-market-news/samsung-asks-court-to-block-illegal-strike-activities-by-unions-4617495",
        "source_name": "Reuters / Investing.com",
        "citation_snippet": "The labor dispute threatened to disrupt operations at a major chipmaker.",
    },
    {
        "country_code": "IN",
        "risk_type": "weather",
        "severity": 4,
        "title": "India boosts coal and gas output as heatwave drives record power demand",
        "summary": "Reuters reported on April 27, 2026 that India's heatwave pushed peak demand to a record level, increasing operational stress for freight, ports, and export activity.",
        "event_date": "2026-04-27",
        "route_code": None,
        "source_url": "https://energy.economictimes.indiatimes.com/news/coal/india-boosts-coal-and-gas-output-as-power-demand-hits-record-peak-in-heatwave/130578534",
        "source_name": "Reuters / ET EnergyWorld",
        "citation_snippet": "Record power demand during the heatwave raised strain across the system.",
    },
)


@dataclass(slots=True)
class ManualExternalRiskSeedResult:
    country_codes: list[str]
    cache_paths: list[Path]
    event_count: int
    score_count: int


def _manual_event_id(country_code: str, title: str) -> str:
    digest = hashlib.sha256(f"manual:{country_code}:{title}".encode("utf-8")).hexdigest()
    return f"manual_{digest[:16]}"


def _build_events() -> list[ExternalRiskEvent]:
    events: list[ExternalRiskEvent] = []
    for item in MANUAL_RISK_ITEMS:
        payload = {
            "origin": "manual_external_risk_snapshot",
            "snapshotDetectedAt": SNAPSHOT_DETECTED_AT,
            "sourceUrl": item["source_url"],
        }
        events.append(
            ExternalRiskEvent(
                event_id=_manual_event_id(str(item["country_code"]), str(item["title"])),
                source_type="manual_snapshot",
                risk_type=str(item["risk_type"]),
                severity=int(item["severity"]),
                title=str(item["title"]),
                summary=str(item["summary"]),
                country_code=str(item["country_code"]),
                route_code=str(item["route_code"]) if item["route_code"] else None,
                affected_supplier_id=None,
                affected_product_id=None,
                event_date=str(item["event_date"]),
                detected_at=SNAPSHOT_DETECTED_AT,
                expires_at=None,
                status="open",
                source_url=str(item["source_url"]),
                source_name=str(item["source_name"]),
                citation_snippet=str(item["citation_snippet"]),
                confidence=0.92,
                payload_json=json.dumps(payload, sort_keys=True),
            )
        )
    return events


def _build_citations(events: list[ExternalRiskEvent]) -> list[Citation]:
    return dedupe_citations(
        [
            Citation(
                title=event.title,
                url=event.source_url or "",
                source_name=event.source_name or "",
                snippet=event.citation_snippet,
            )
            for event in events
            if event.source_url and event.source_name
        ]
    )


def _build_output(
    *,
    requested_country_codes: list[str],
    all_events: list[ExternalRiskEvent],
    all_citations: list[Citation],
    catalog_repository: CatalogRepository,
    score_items: list[object],
) -> ExternalRiskAgentOutput:
    scoped_codes = sorted({code.strip().upper() for code in requested_country_codes if code.strip()})
    scoped_events = [event for event in all_events if (event.country_code or "").upper() in scoped_codes]
    scoped_scores = [score for score in score_items if score.country_code in scoped_codes]
    scoped_citations = [
        citation
        for citation in all_citations
        if any(citation.url == event.source_url for event in scoped_events if event.source_url)
    ]
    affected_suppliers = [
        AffectedSupplierRef(
            supplier_id=supplier.id,
            supplier_code=supplier.supplier_code,
            name=supplier.name,
            country_code=supplier.country_code,
        )
        for supplier in catalog_repository.list_suppliers_by_country_codes(scoped_codes)
    ]
    affected_products = [
        AffectedProductRef(
            product_id=product.id,
            sku=product.sku,
            name=product.name,
            category=product.category,
        )
        for product in catalog_repository.list_products_by_supplier_countries(scoped_codes)
    ]
    country_list = ", ".join(country_name(code) for code in scoped_codes)
    summary = (
        f"Curated local external-risk snapshot covering {country_list}."
        if scoped_scores
        else f"No curated local external-risk events are stored for {country_list}."
    )
    return ExternalRiskAgentOutput(
        risk_events=scoped_events,
        country_scores=scoped_scores,
        citations=scoped_citations,
        summary=summary,
        highest_severity=max((event.severity for event in scoped_events), default=1),
        affected_suppliers=affected_suppliers,
        affected_products=affected_products,
        limitations=[SNAPSHOT_SUMMARY_NOTE],
        data_source="cached",
    )


def persist_manual_external_risk_snapshot(
    *,
    settings: Settings,
    storage: StorageManager,
    database: SQLiteConnectionFactory,
) -> ManualExternalRiskSeedResult:
    catalog_repository = CatalogRepository(database)
    risk_repository = RiskRepository(database)
    all_events = _build_events()
    event_country_codes = sorted({event.country_code for event in all_events if event.country_code})
    agent = ExternalRiskAgent(
        settings=settings,
        storage=storage,
        database=database,
        search_adapter=NullSearchAdapter(),
    )
    all_scores = agent._aggregate_country_scores(event_country_codes, all_events)
    for score in all_scores:
        score.score_date = SNAPSHOT_DETECTED_AT
    all_citations = _build_citations(all_events)

    with database.transaction() as connection:
        for event in all_events:
            risk_repository.upsert_risk_event(event, connection=connection)
        for score in all_scores:
            risk_repository.upsert_country_score(score, connection=connection)

    cache_paths: list[Path] = []
    scope_codes = sorted({*catalog_repository.list_all_supplier_country_codes(), *map_watchlist_country_codes()})
    requested_scopes = [scope_codes, *([[code] for code in event_country_codes])]
    for requested_country_codes in requested_scopes:
        output = _build_output(
            requested_country_codes=requested_country_codes,
            all_events=all_events,
            all_citations=all_citations,
            catalog_repository=catalog_repository,
            score_items=all_scores,
        )
        input_model = ExternalRiskAgentInput(country_codes=requested_country_codes)
        normalized_codes = agent._collect_country_codes(input_model)
        cache_key = agent._build_cache_key(input_model, normalized_codes)
        cache_paths.append(
            storage.write_external_risk_cache(
                cache_key,
                {
                    "cachedAt": SNAPSHOT_DETECTED_AT,
                    "refreshDisabled": True,
                    "output": output.model_dump(mode="json"),
                },
            )
        )

    return ManualExternalRiskSeedResult(
        country_codes=event_country_codes,
        cache_paths=cache_paths,
        event_count=len(all_events),
        score_count=len(all_scores),
    )
