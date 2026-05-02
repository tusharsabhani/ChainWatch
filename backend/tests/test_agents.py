from __future__ import annotations

import csv
from datetime import datetime, timezone
import os
from pathlib import Path

import app.agents.external_risk as external_risk_module
from app.adapters.search import NullSearchAdapter, SearchAdapter
from app.agents.demand import DemandAgent
from app.agents.external_risk import ExternalRiskAgent
from app.agents.fulfillment import FulfillmentAgent
from app.agents.inventory import InventoryAgent
from app.db.repositories.agent_run_repository import AgentRunRepository
from app.db.repositories.catalog_repository import CatalogRepository
from app.db.repositories.system_repository import SystemRepository
from app.schemas.agents import (
    AgentTriggerType,
    DemandAgentInput,
    DemandSignal,
    ExternalRiskAgentInput,
    FulfillmentAgentInput,
    InventoryAgentInput,
)
from app.schemas.imports import ImportType
from app.services.imports.service import CSVImportService


def _write_csv(destination: Path, rows: list[dict[str, object]]) -> Path:
    fieldnames = list(rows[0].keys())
    with destination.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return destination


class FakeSearchAdapter(SearchAdapter):
    def __init__(self, results_by_country: dict[str, list[dict[str, object]]]) -> None:
        self.results_by_country = results_by_country
        self.queries_by_country: dict[str, str] = {}

    def is_configured(self) -> bool:
        return True

    def search(self, query: str, **kwargs):
        country_code = str(kwargs.get("country_code", "")).upper()
        self.queries_by_country[country_code] = query
        return list(self.results_by_country.get(country_code, []))


def test_demand_agent_returns_structured_summary_and_trace(seeded_runtime) -> None:
    catalog_repository = CatalogRepository(seeded_runtime.database)
    products = catalog_repository.list_products_by_ids([1, 2])

    agent = DemandAgent(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
    )
    output = agent.run(
        DemandAgentInput(
            product_ids=[product.id for product in products],
            trigger_type=AgentTriggerType.DASHBOARD,
            trigger_ref="demand-test",
        )
    )

    assert output.historical_trend
    assert output.forecasted_units > 0
    assert 1.0 <= output.demand_risk_score <= 5.0
    assert output.low_confidence is False

    run_repository = AgentRunRepository(seeded_runtime.database)
    runs = run_repository.list_runs_for_agent("Demand Agent")
    assert len(runs) == 1
    assert runs[0]["status"] == "completed"


def test_demand_agent_marks_sparse_history_low_confidence(runtime, tmp_path: Path) -> None:
    import_service = CSVImportService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
    )
    import_service.import_csv(
        ImportType.SUPPLIERS,
        _write_csv(
            tmp_path / "suppliers.csv",
            [
                {
                    "supplier_code": "SUP-001",
                    "name": "Starter Supply",
                    "country_code": "IN",
                    "region": "APAC",
                    "lead_time_days": 10,
                    "reliability_score": 90.0,
                    "active": 1,
                }
            ],
        ),
    )
    import_service.import_csv(
        ImportType.PRODUCTS,
        _write_csv(
            tmp_path / "products.csv",
            [
                {
                    "sku": "SKU-LOW-HISTORY",
                    "name": "Pilot SKU",
                    "category": "Pilot",
                    "brand": "ChainWatch Demo",
                    "status": "active",
                    "origin_country_code": "IN",
                    "default_supplier_code": "SUP-001",
                    "alternate_supplier_codes": "",
                }
            ],
        ),
    )
    import_service.import_csv(
        ImportType.SALES,
        _write_csv(
            tmp_path / "sales.csv",
            [
                {
                    "product_sku": "SKU-LOW-HISTORY",
                    "sales_date": "2026-03-01",
                    "channel": "web",
                    "region_code": "APAC",
                    "units_sold": 12,
                    "gross_revenue": 240.0,
                    "net_revenue": 230.0,
                    "returns_qty": 0,
                    "promo_flag": 0,
                    "stockout_flag": 0,
                },
                {
                    "product_sku": "SKU-LOW-HISTORY",
                    "sales_date": "2026-04-01",
                    "channel": "web",
                    "region_code": "APAC",
                    "units_sold": 14,
                    "gross_revenue": 280.0,
                    "net_revenue": 270.0,
                    "returns_qty": 0,
                    "promo_flag": 1,
                    "stockout_flag": 0,
                },
            ],
        ),
    )

    catalog_repository = CatalogRepository(runtime.database)
    product = catalog_repository.get_product_by_sku("SKU-LOW-HISTORY")
    assert product is not None

    agent = DemandAgent(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
    )
    output = agent.run(
        DemandAgentInput(
            product_ids=[product.id],
            trigger_type=AgentTriggerType.PRODUCT,
            trigger_ref="low-confidence-test",
        )
    )

    assert output.low_confidence is True
    assert output.supporting_notes


def test_inventory_agent_uses_demand_signal_and_returns_deterministic_status(seeded_runtime) -> None:
    agent = InventoryAgent(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
    )
    output = agent.run(
        InventoryAgentInput(
            product_ids=[1, 2],
            demand_signals=[
                DemandSignal(
                    product_id=1,
                    forecast_window_days=30,
                    forecasted_units=180,
                    demand_risk_score=4.1,
                ),
                DemandSignal(
                    product_id=2,
                    forecast_window_days=30,
                    forecasted_units=140,
                    demand_risk_score=3.6,
                ),
            ],
            trigger_type=AgentTriggerType.PRODUCT,
            trigger_ref="inventory-test",
        )
    )

    assert output.current_on_hand > 0
    assert output.reorder_point > 0
    assert 1.0 <= output.stockout_risk_score <= 5.0
    assert output.inventory_status in {"healthy", "watch", "reorder", "critical"}
    assert output.partial is False


def test_fulfillment_agent_aggregates_regions_and_uses_external_context(seeded_runtime) -> None:
    agent = FulfillmentAgent(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
    )
    output = agent.run(
        FulfillmentAgentInput(
            product_ids=[1, 2, 3, 4],
            trigger_type=AgentTriggerType.DASHBOARD,
            trigger_ref="fulfillment-test",
            external_risk_events=[],
        )
    )

    assert len(output.regional_status) >= 2
    assert output.backlog_orders > 0
    assert 0.0 <= output.on_time_rate <= 1.0
    assert 1.0 <= output.fulfillment_risk_score <= 5.0
    assert 1 <= output.sla_risk_level <= 5


def test_external_risk_agent_persists_events_scores_and_cache(seeded_runtime) -> None:
    fake_adapter = FakeSearchAdapter(
        {
            "IN": [
                {
                    "title": "Port delays disrupt inbound shipments in India",
                    "url": "https://example.com/in-port-delay",
                    "source_name": "Global Trade Watch",
                    "snippet": "Major shipping delays are affecting port throughput and container pickup windows.",
                    "risk_type": "logistics",
                    "severity": 4,
                    "event_date": "2026-05-01",
                }
            ],
            "VN": [
                {
                    "title": "Labor strike slows factory output in Vietnam",
                    "url": "https://example.com/vn-strike",
                    "source_name": "Supply Ledger",
                    "snippet": "A labor strike is slowing production and increasing lead time risk for exporters.",
                    "risk_type": "labor",
                    "severity": 5,
                    "event_date": "2026-05-01",
                }
            ],
        }
    )
    live_agent = ExternalRiskAgent(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
        search_adapter=fake_adapter,
    )
    live_output = live_agent.run(
        ExternalRiskAgentInput(
            country_codes=["IN", "VN"],
            trigger_type=AgentTriggerType.MAP,
            trigger_ref="external-live",
        )
    )

    assert live_output.data_source == "fresh"
    assert len(live_output.risk_events) == 2
    assert len(live_output.country_scores) == 2
    assert len(live_output.citations) == 2
    assert live_output.affected_suppliers
    assert live_output.affected_products

    system_repository = SystemRepository(seeded_runtime.database)
    assert system_repository.count_rows("risk_events") == 2
    assert system_repository.count_rows("country_risk_scores") == 2

    cached_agent = ExternalRiskAgent(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
        search_adapter=NullSearchAdapter(),
    )
    cached_output = cached_agent.run(
        ExternalRiskAgentInput(
            country_codes=["IN", "VN"],
            trigger_type=AgentTriggerType.MAP,
            trigger_ref="external-cached",
        )
    )

    assert cached_output.data_source == "cached"
    assert len(cached_output.risk_events) == 2
    assert cached_output.limitations

    run_repository = AgentRunRepository(seeded_runtime.database)
    runs = run_repository.list_runs_for_agent("External Risk Agent")
    assert len(runs) == 2
    assert runs[0]["status"] == "completed"
    assert runs[1]["status"] == "partial"


def test_external_risk_search_query_uses_country_name_and_hotspot_terms(seeded_runtime) -> None:
    fake_adapter = FakeSearchAdapter(
        {
            "IN": [
                {
                    "title": "India heatwave strains logistics",
                    "url": "https://example.com/in-heatwave",
                    "source_name": "Weather Desk",
                    "snippet": "Extreme heat is stressing freight operations and power usage.",
                    "event_date": "2026-05-01",
                }
            ],
            "IR": [
                {
                    "title": "Hormuz shipping remains constrained",
                    "url": "https://example.com/ir-hormuz",
                    "source_name": "Maritime Desk",
                    "snippet": "Traffic through the Strait of Hormuz remains far below normal levels.",
                    "event_date": "2026-05-01",
                }
            ],
        }
    )
    agent = ExternalRiskAgent(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
        search_adapter=fake_adapter,
    )
    output = agent.run(
        ExternalRiskAgentInput(
            country_codes=["IN", "IR"],
            trigger_type=AgentTriggerType.MAP,
            trigger_ref="query-shape-test",
        )
    )

    assert output.data_source == "fresh"
    assert "India (IN)" in fake_adapter.queries_by_country["IN"]
    assert "heatwave" in fake_adapter.queries_by_country["IN"].lower()
    assert "Iran (IR)" in fake_adapter.queries_by_country["IR"]
    assert "strait of hormuz" in fake_adapter.queries_by_country["IR"].lower()


def test_external_risk_cache_stays_fresh_for_the_same_day(seeded_runtime, monkeypatch) -> None:
    fake_adapter = FakeSearchAdapter(
        {
            "IN": [
                {
                    "title": "Port delays disrupt inbound shipments in India",
                    "url": "https://example.com/in-port-delay",
                    "source_name": "Global Trade Watch",
                    "snippet": "Major shipping delays are affecting port throughput and container pickup windows.",
                    "risk_type": "logistics",
                    "severity": 4,
                    "event_date": "2026-05-01",
                }
            ]
        }
    )
    agent = ExternalRiskAgent(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
        search_adapter=fake_adapter,
    )
    input_model = ExternalRiskAgentInput(
        country_codes=["IN"],
        trigger_type=AgentTriggerType.MAP,
        trigger_ref="same-day-cache",
    )
    agent.run(input_model)

    cache_key = agent._build_cache_key(input_model, ["IN"])
    cache_path = seeded_runtime.storage.external_risk_cache_path(cache_key)
    cache_timestamp = datetime(2026, 5, 1, 1, 0, tzinfo=timezone.utc).timestamp()
    os.utime(cache_path, (cache_timestamp, cache_timestamp))

    monkeypatch.setattr(
        external_risk_module,
        "_utc_now",
        lambda: datetime(2026, 5, 1, 18, 0, tzinfo=timezone.utc),
    )

    assert agent._is_cache_fresh(cache_path, freshness_policy_hours=1) is True
