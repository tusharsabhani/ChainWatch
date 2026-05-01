from __future__ import annotations

import pytest

from app.services.storage import StorageManager


def test_storage_manager_resolves_safe_paths(settings) -> None:
    storage = StorageManager(settings)
    storage.ensure_runtime_paths()

    resolved = storage.resolve_in_data("reports/json/example.json")

    assert resolved == settings.reports_json_dir / "example.json"


def test_storage_manager_rejects_paths_outside_data_root(settings) -> None:
    storage = StorageManager(settings)
    storage.ensure_runtime_paths()

    with pytest.raises(ValueError):
        storage.resolve_in_data("../escape.json")


def test_storage_manager_writes_and_reads_external_risk_cache(settings) -> None:
    storage = StorageManager(settings)
    storage.ensure_runtime_paths()

    storage.write_external_risk_cache("country:IN", {"severity": 3, "summary": "Delay risk"})

    cached_payload = storage.read_external_risk_cache("country:IN")

    assert cached_payload == {
        "severity": 3,
        "summary": "Delay risk",
    }
