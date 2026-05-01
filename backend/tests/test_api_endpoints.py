from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.adapters.search import SearchAdapter
from app.agents.external_risk import ExternalRiskAgent
from app.main import create_app
from app.schemas.agents import AgentTriggerType, ExternalRiskAgentInput
from app.services.imports.seed import DemoSeedService
from app.services.runtime import bootstrap_runtime


class FakeSearchAdapter(SearchAdapter):
    def __init__(self, results_by_country: dict[str, list[dict[str, object]]]) -> None:
        self.results_by_country = results_by_country

    def is_configured(self) -> bool:
        return True

    def search(self, query: str, **kwargs):
        country_code = str(kwargs.get("country_code", "")).upper()
        return list(self.results_by_country.get(country_code, []))


def _fake_search_adapter() -> FakeSearchAdapter:
    return FakeSearchAdapter(
        {
            "IN": [
                {
                    "title": "India port congestion slows inbound shipments",
                    "url": "https://example.com/in-port",
                    "source_name": "Trade Desk",
                    "snippet": "Port congestion is slowing unloading and inland transfers.",
                    "risk_type": "logistics",
                    "severity": 4,
                    "event_date": "2026-05-01",
                }
            ],
            "VN": [
                {
                    "title": "Vietnam labor action affects factory output",
                    "url": "https://example.com/vn-labor",
                    "source_name": "Supply Pulse",
                    "snippet": "Labor action is constraining exporter throughput and increasing lead times.",
                    "risk_type": "labor",
                    "severity": 5,
                    "event_date": "2026-05-01",
                }
            ],
        }
    )


@pytest.fixture()
def seeded_api_app(settings):
    runtime = bootstrap_runtime(settings)
    DemoSeedService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
    ).seed_demo_data()
    return create_app(settings=settings, search_adapter=_fake_search_adapter())


def _write_csv(destination: Path, rows: list[dict[str, object]]) -> Path:
    fieldnames = list(rows[0].keys())
    with destination.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return destination


def test_dashboard_endpoints_return_summary_and_alerts(seeded_api_app) -> None:
    with TestClient(seeded_api_app) as client:
        summary_response = client.get("/api/dashboard/summary", params={"severityMin": 3})
        alerts_response = client.get("/api/dashboard/alerts", params={"severityMin": 4})

    assert summary_response.status_code == 200
    summary_payload = summary_response.json()
    assert summary_payload["kpis"]["activeAlerts"] >= 2
    assert summary_payload["topRiskProducts"]
    assert summary_payload["countryExposure"]
    assert summary_payload["lastUpdatedAt"]
    assert summary_payload["freshness"]["dataSource"] in {"fresh", "cached"}

    assert alerts_response.status_code == 200
    alerts_payload = alerts_response.json()
    assert alerts_payload["items"]
    assert alerts_payload["total"] >= 1
    assert alerts_payload["items"][0]["severity"] >= 4
    assert alerts_payload["freshness"]["dataSource"] in {"fresh", "cached"}


def test_map_endpoints_return_country_summary_and_detail(seeded_api_app) -> None:
    with TestClient(seeded_api_app) as client:
        countries_response = client.get("/api/map/countries", params={"severityMin": 3})
        detail_response = client.get("/api/map/countries/IN")
        missing_response = client.get("/api/map/countries/ZZ")

    assert countries_response.status_code == 200
    countries_payload = countries_response.json()
    assert any(item["countryCode"] == "IN" for item in countries_payload["items"])

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["country"]["countryCode"] == "IN"
    assert detail_payload["issues"]
    assert detail_payload["freshness"]["dataSource"] in {"fresh", "cached"}

    assert missing_response.status_code == 404
    assert missing_response.json()["error"]["code"] == "country_not_found"


def test_product_endpoints_return_search_and_detail_payloads(seeded_api_app) -> None:
    with TestClient(seeded_api_app) as client:
        list_response = client.get("/api/products", params={"riskMin": 2})
        detail_response = client.get("/api/products/1")
        missing_response = client.get("/api/products/999")

    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["items"]
    assert "riskScore" in list_payload["items"][0]

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["product"]["id"] == 1
    assert detail_payload["suppliers"]
    assert detail_payload["linkedRiskEvents"]
    assert detail_payload["freshness"]["dataSource"] in {"fresh", "cached"}

    assert missing_response.status_code == 404
    assert missing_response.json()["error"]["code"] == "product_not_found"


def test_chat_endpoints_create_session_persist_messages_and_return_answer(seeded_api_app) -> None:
    with TestClient(seeded_api_app) as client:
        create_response = client.post(
            "/api/chat/sessions",
            json={"contextScope": "global"},
        )
        assert create_response.status_code == 200
        session_id = create_response.json()["id"]

        list_response = client.get("/api/chat/sessions")
        post_response = client.post(
            "/api/chat/messages",
            json={
                "sessionId": session_id,
                "message": "Why are shipping delays and labor risk rising this week?",
            },
        )
        history_response = client.get(f"/api/chat/sessions/{session_id}/messages")

    assert list_response.status_code == 200
    assert any(item["id"] == session_id for item in list_response.json()["items"])

    assert post_response.status_code == 200
    post_payload = post_response.json()
    assert post_payload["assistantMessage"]["usedAgents"]
    assert post_payload["assistantMessage"]["citations"]

    assert history_response.status_code == 200
    history_payload = history_response.json()
    assert len(history_payload["messages"]) == 2
    assert history_payload["messages"][-1]["role"] == "assistant"


def test_report_endpoints_generate_list_and_detail(seeded_api_app) -> None:
    with TestClient(seeded_api_app) as client:
        generate_response = client.post(
            "/api/reports/generate",
            json={
                "scopeType": "country",
                "scopeId": "IN",
                "reportType": "country_risk",
            },
        )
        assert generate_response.status_code == 200
        generate_payload = generate_response.json()
        report_id = generate_payload["id"]
        assert generate_payload["status"] == "queued"

        list_response = client.get("/api/reports")
        detail_response = client.get(f"/api/reports/{report_id}")

    assert list_response.status_code == 200
    assert any(item["id"] == report_id for item in list_response.json()["items"])

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["id"] == report_id
    assert detail_payload["jsonPath"]
    assert detail_payload["markdownPreview"]
    assert detail_payload["freshness"]["dataSource"] == "generated"


def test_import_endpoints_list_runs_and_accept_local_file_reference(seeded_api_app, tmp_path: Path) -> None:
    source_path = _write_csv(
        tmp_path / "suppliers.csv",
        [
            {
                "supplier_code": "SUP-TEST-01",
                "name": "Test Supplier",
                "country_code": "US",
                "region": "NA",
                "lead_time_days": 9,
                "reliability_score": 93.0,
                "active": 1,
            }
        ],
    )

    with TestClient(seeded_api_app) as client:
        list_before = client.get("/api/imports")
        import_response = client.post(
            "/api/imports/suppliers",
            json={"filePath": str(source_path)},
        )
        list_after = client.get("/api/imports")
        invalid_response = client.post(
            "/api/imports/suppliers",
            json={"filePath": str(tmp_path / 'missing.csv')},
        )

    assert list_before.status_code == 200
    assert len(list_before.json()["items"]) >= 5

    assert import_response.status_code == 200
    import_payload = import_response.json()
    assert import_payload["importType"] == "suppliers"
    assert import_payload["status"] == "completed"

    assert list_after.status_code == 200
    assert len(list_after.json()["items"]) == len(list_before.json()["items"]) + 1

    assert invalid_response.status_code == 400
    assert invalid_response.json()["error"]["code"] == "invalid_import_file"


def test_stale_external_risk_cache_surfaces_freshness_and_schedules_refresh(settings) -> None:
    runtime = bootstrap_runtime(settings)
    DemoSeedService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
    ).seed_demo_data()
    app = create_app(settings=settings, search_adapter=_fake_search_adapter())

    with TestClient(app) as client:
        first_response = client.get("/api/map/countries")
        assert first_response.status_code == 200

        agent = ExternalRiskAgent(
            settings=runtime.settings,
            storage=runtime.storage,
            database=runtime.database,
            search_adapter=_fake_search_adapter(),
        )
        cache_key = agent._build_cache_key(
            ExternalRiskAgentInput(
                country_codes=["IN", "MX", "US", "VN"],
                trigger_type=AgentTriggerType.MAP,
                trigger_ref="map-countries",
                freshness_policy_hours=runtime.settings.external_risk_cache_ttl_hours,
            ),
            ["IN", "MX", "US", "VN"],
        )
        cache_path = runtime.storage.external_risk_cache_path(cache_key)
        stale_timestamp = cache_path.stat().st_mtime - (runtime.settings.external_risk_cache_ttl_hours * 7200)
        os.utime(cache_path, (stale_timestamp, stale_timestamp))

        second_response = client.get("/api/map/countries")

    assert second_response.status_code == 200
    second_payload = second_response.json()
    assert second_payload["freshness"]["dataSource"] == "cached"
    assert second_payload["freshness"]["isStale"] is True
    assert second_payload["freshness"]["refreshScheduled"] is True
