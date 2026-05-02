from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import BackgroundTasks

from app.adapters.search import NullSearchAdapter, SearchAdapter
from app.agents.external_risk import ExternalRiskAgent
from app.config import Settings
from app.db.connection import SQLiteConnectionFactory
from app.schemas.agents import AgentTriggerType, ExternalRiskAgentInput, ExternalRiskAgentOutput
from app.schemas.common import FreshnessInfo
from app.services.storage import StorageManager


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class ExternalRiskEnvelope:
    output: ExternalRiskAgentOutput
    freshness: FreshnessInfo


class ExternalRiskService:
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
        self.search_adapter = search_adapter or NullSearchAdapter()
        self.agent = ExternalRiskAgent(
            settings=settings,
            storage=storage,
            database=database,
            search_adapter=self.search_adapter,
        )

    def load(
        self,
        input_model: ExternalRiskAgentInput,
        *,
        background_tasks: BackgroundTasks | None = None,
        prefer_cached: bool = True,
    ) -> ExternalRiskEnvelope:
        country_codes = self.agent._collect_country_codes(input_model)
        if not country_codes:
            output = self.agent.run(input_model)
            return ExternalRiskEnvelope(
                output=output,
                freshness=FreshnessInfo(
                    data_source=output.data_source,
                    last_updated_at=None,
                    cache_updated_at=None,
                    is_stale=False,
                    refresh_scheduled=False,
                ),
            )

        cache_key = self.agent._build_cache_key(input_model, country_codes)
        cache_path = self.storage.external_risk_cache_path(cache_key)
        cached_payload = self.storage.read_external_risk_cache(cache_key)
        cached_output: ExternalRiskAgentOutput | None = None
        cache_updated_at: str | None = None
        if cached_payload:
            cache_updated_at = str(cached_payload.get("cachedAt")) if "cachedAt" in cached_payload else None
            if "output" in cached_payload:
                cached_output = ExternalRiskAgentOutput.model_validate(cached_payload["output"])
            else:
                cached_output = ExternalRiskAgentOutput.model_validate(cached_payload)
        refresh_disabled = bool(cached_payload.get("refreshDisabled")) if isinstance(cached_payload, dict) else False

        cache_is_fresh = self.agent._is_cache_fresh(cache_path, input_model.freshness_policy_hours)
        if prefer_cached and cached_output is not None:
            refresh_scheduled = False
            limitations = list(cached_output.limitations)
            if not cache_is_fresh:
                limitations.append(
                    "Serving stale cached external risk data while a refresh runs in the background."
                    if not refresh_disabled
                    else "Serving stale cached external risk data from a pinned local snapshot."
                )
                if (
                    background_tasks is not None
                    and self.settings.external_risk_refresh_enabled
                    and not refresh_disabled
                    and self.search_adapter.is_configured()
                ):
                    background_tasks.add_task(self.refresh, input_model)
                    refresh_scheduled = True

            output = cached_output.model_copy(
                update={
                    "data_source": "cached",
                    "limitations": list(dict.fromkeys(limitations)),
                }
            )
            return ExternalRiskEnvelope(
                output=output,
                freshness=FreshnessInfo(
                    data_source="cached",
                    last_updated_at=self._last_updated_at(output, cache_updated_at),
                    cache_updated_at=cache_updated_at,
                    is_stale=not cache_is_fresh,
                    refresh_scheduled=refresh_scheduled,
                ),
            )

        output = self.agent.run(input_model)
        cache_updated_at = cache_updated_at or _utc_now_iso()
        return ExternalRiskEnvelope(
            output=output,
            freshness=FreshnessInfo(
                data_source=output.data_source,
                last_updated_at=self._last_updated_at(output, cache_updated_at),
                cache_updated_at=cache_updated_at if output.data_source != "empty" else None,
                is_stale=False,
                refresh_scheduled=False,
            ),
        )

    def refresh(self, input_model: ExternalRiskAgentInput) -> ExternalRiskAgentOutput:
        refresh_input = input_model.model_copy(
            update={
                "trigger_type": AgentTriggerType.REFRESH,
                "trigger_ref": input_model.trigger_ref or "background-refresh",
            }
        )
        return self.agent.run(refresh_input)

    def _last_updated_at(
        self,
        output: ExternalRiskAgentOutput,
        cache_updated_at: str | None,
    ) -> str | None:
        if output.risk_events:
            return max(event.detected_at for event in output.risk_events)
        return cache_updated_at
