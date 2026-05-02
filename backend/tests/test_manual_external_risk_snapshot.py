from __future__ import annotations

import os
from datetime import datetime, timezone

import app.agents.external_risk as external_risk_agent_module
from fastapi import BackgroundTasks
from app.adapters.search import SearchAdapter
from app.agents.external_risk import ExternalRiskAgent
from app.db.repositories.catalog_repository import CatalogRepository
from app.db.repositories.system_repository import SystemRepository
from app.schemas.agents import ExternalRiskAgentInput
from app.services.countries import map_watchlist_country_codes
from app.services.external_risk import ExternalRiskService
from app.services.manual_external_risk_snapshot import persist_manual_external_risk_snapshot


class ConfiguredNoopSearchAdapter(SearchAdapter):
    def is_configured(self) -> bool:
        return True

    def search(self, query: str, **kwargs):
        return []


def test_manual_external_risk_snapshot_persists_and_skips_refresh(seeded_runtime, monkeypatch) -> None:
    result = persist_manual_external_risk_snapshot(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
    )

    assert result.country_codes == ["AE", "IN", "IR", "KR", "OM", "SA"]
    assert result.event_count == 6
    assert result.score_count == 6
    assert len(result.cache_paths) == 7

    system_repository = SystemRepository(seeded_runtime.database)
    assert system_repository.count_rows("risk_events") == 6
    assert system_repository.count_rows("country_risk_scores") == 6

    scope_codes = sorted(
        {
            *CatalogRepository(seeded_runtime.database).list_all_supplier_country_codes(),
            *map_watchlist_country_codes(),
        }
    )
    agent = ExternalRiskAgent(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
    )
    input_model = ExternalRiskAgentInput(country_codes=scope_codes)
    cache_key = agent._build_cache_key(input_model, scope_codes)
    cache_path = seeded_runtime.storage.external_risk_cache_path(cache_key)
    cached_payload = seeded_runtime.storage.read_external_risk_cache(cache_key)

    assert cache_path.exists()
    assert cached_payload["refreshDisabled"] is True
    assert cached_payload["output"]["country_scores"]

    stale_timestamp = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc).timestamp()
    os.utime(cache_path, (stale_timestamp, stale_timestamp))
    monkeypatch.setattr(
        external_risk_agent_module,
        "_utc_now",
        lambda: datetime(2026, 5, 3, 12, 0, tzinfo=timezone.utc),
    )

    service = ExternalRiskService(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
        search_adapter=ConfiguredNoopSearchAdapter(),
    )
    envelope = service.load(
        ExternalRiskAgentInput(country_codes=scope_codes),
        background_tasks=BackgroundTasks(),
        prefer_cached=True,
    )

    assert envelope.freshness.is_stale is True
    assert envelope.freshness.refresh_scheduled is False
    assert any("pinned local snapshot" in limitation for limitation in envelope.output.limitations)
