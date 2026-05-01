from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.adapters.search import SearchAdapter
from app.main import create_app
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
def scenario_app(settings):
    runtime = bootstrap_runtime(settings)
    DemoSeedService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
    ).seed_demo_data()
    return create_app(settings=settings, search_adapter=_fake_search_adapter())


def test_dashboard_to_product_detail_consistency_scenario(scenario_app) -> None:
    with TestClient(scenario_app) as client:
        summary_response = client.get("/api/dashboard/summary", params={"severityMin": 3})
        assert summary_response.status_code == 200
        summary_payload = summary_response.json()

        top_product = summary_payload["topRiskProducts"][0]
        detail_response = client.get(f"/api/products/{top_product['productId']}")

    assert detail_response.status_code == 200
    detail_payload = detail_response.json()
    assert detail_payload["product"]["id"] == top_product["productId"]
    assert detail_payload["product"]["sku"] == top_product["sku"]
    assert detail_payload["product"]["name"] == top_product["name"]
    assert detail_payload["freshness"]["dataSource"] in {"fresh", "cached"}
    assert detail_payload["demand"]["demandRiskScore"] >= 1.0
    assert detail_payload["inventory"]["stockoutRiskScore"] >= 1.0
    assert detail_payload["fulfillment"]["fulfillmentRiskScore"] >= 1.0


def test_map_country_chat_and_report_scenario(scenario_app) -> None:
    with TestClient(scenario_app) as client:
        country_detail_response = client.get("/api/map/countries/IN")
        assert country_detail_response.status_code == 200
        country_detail = country_detail_response.json()
        assert country_detail["issues"]

        session_response = client.post(
            "/api/chat/sessions",
            json={"contextScope": "country", "contextId": "IN"},
        )
        assert session_response.status_code == 200
        session_id = session_response.json()["id"]

        chat_response = client.post(
            "/api/chat/messages",
            json={
                "sessionId": session_id,
                "message": "What should I watch in this country right now?",
            },
        )
        assert chat_response.status_code == 200
        chat_payload = chat_response.json()

        country_report_response = client.post(
            "/api/reports/generate",
            json={
                "scopeType": "country",
                "scopeId": "IN",
                "reportType": "country_risk",
            },
        )
        assert country_report_response.status_code == 200
        country_report_id = country_report_response.json()["id"]
        country_report_detail = client.get(f"/api/reports/{country_report_id}")

        chat_export_response = client.post(
            "/api/reports/generate",
            json={
                "scopeType": "chat",
                "scopeId": session_id,
                "reportType": "chat_export",
            },
        )
        assert chat_export_response.status_code == 200
        chat_report_id = chat_export_response.json()["id"]
        chat_report_detail = client.get(f"/api/reports/{chat_report_id}")

    assert "External Risk Agent" in chat_payload["assistantMessage"]["usedAgents"]
    assert chat_payload["assistantMessage"]["citations"]

    assert country_report_detail.status_code == 200
    country_report_payload = country_report_detail.json()
    assert country_report_payload["scopeType"] == "country"
    assert country_report_payload["scopeId"] == "IN"
    assert country_report_payload["markdownPreview"]

    assert chat_report_detail.status_code == 200
    chat_report_payload = chat_report_detail.json()
    assert chat_report_payload["scopeType"] == "chat"
    assert chat_report_payload["scopeId"] == session_id
    assert chat_report_payload["markdownPreview"]
