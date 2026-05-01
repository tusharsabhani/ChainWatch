from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoint_returns_expected_shape(app) -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "ok"
    assert payload["appVersion"] == "0.1.0"
    assert payload["database"] == {
        "status": "connected",
        "path": "data/app.db",
    }
    assert payload["storage"] == {
        "reportsJsonPath": "data/reports/json",
        "reportsMarkdownPath": "data/reports/markdown",
        "importsPath": "data/imports/raw",
        "cachePath": "data/cache/external_risk",
    }
    assert payload["providers"] == {
        "llmConfigured": False,
        "searchConfigured": False,
    }
    assert payload["backgroundTasks"] == {
        "reportsEnabled": True,
        "externalRiskRefreshEnabled": True,
    }

