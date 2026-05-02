from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.adapters.search import NullSearchAdapter, SearchAdapter
from app.agents.base import BaseAgent
from app.config import Settings
from app.db.connection import SQLiteConnectionFactory
from app.db.repositories.catalog_repository import CatalogRepository
from app.db.repositories.risk_repository import RiskRepository
from app.schemas.agents import (
    AffectedProductRef,
    AffectedSupplierRef,
    AgentRunStatus,
    Citation,
    CountryRiskScore,
    ExternalRiskAgentInput,
    ExternalRiskAgentOutput,
    ExternalRiskEvent,
)
from app.services.citations import dedupe_citations, normalize_citation
from app.services.countries import country_name, country_search_focus
from app.services.scoring import average, clamp
from app.services.storage import StorageManager

RISK_TYPES = ("geopolitical", "tariff", "logistics", "weather", "labor")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExternalRiskAgent(BaseAgent):
    def __init__(
        self,
        *,
        settings: Settings,
        storage: StorageManager,
        database: SQLiteConnectionFactory,
        search_adapter: SearchAdapter | None = None,
    ) -> None:
        super().__init__(
            agent_name="External Risk Agent",
            settings=settings,
            storage=storage,
            database=database,
        )
        self.catalog_repository = CatalogRepository(database)
        self.risk_repository = RiskRepository(database)
        self.search_adapter = search_adapter or NullSearchAdapter()

    def run(self, input_model: ExternalRiskAgentInput) -> ExternalRiskAgentOutput:
        trace = self._start_trace(
            trigger_type=input_model.trigger_type,
            trigger_ref=input_model.trigger_ref,
            input_payload=input_model,
        )

        country_codes = self._collect_country_codes(input_model)
        if not country_codes:
            output = ExternalRiskAgentOutput(
                risk_events=[],
                country_scores=[],
                citations=[],
                summary="No countries were provided for external risk analysis.",
                highest_severity=1,
                affected_suppliers=[],
                affected_products=[],
                limitations=["No country codes or supplier countries were provided."],
                data_source="empty",
            )
            self._finish_trace(
                trace,
                status=self._trace_status(partial=True),
                output_payload=output,
            )
            return output

        cache_key = self._build_cache_key(input_model, country_codes)
        cache_path = self.storage.external_risk_cache_path(cache_key)
        cached_output = self._read_cached_output(cache_key)
        cache_is_fresh = self._is_cache_fresh(cache_path, input_model.freshness_policy_hours)

        if not self.search_adapter.is_configured():
            output = self._cached_or_empty_output(
                cached_output=cached_output,
                cache_is_fresh=cache_is_fresh,
                limitation="Search provider is not configured; returned cached results if available.",
            )
            self._finish_trace(
                trace,
                status=self._trace_status(partial=output.data_source != "fresh"),
                output_payload=output,
            )
            return output

        try:
            events: list[ExternalRiskEvent] = []
            citations: list[Citation] = []
            for country_code in country_codes:
                query = self._build_search_query(
                    country_code=country_code,
                    route_hints=input_model.route_hints,
                    product_category=input_model.product_category,
                )
                search_results = self.search_adapter.search(query, country_code=country_code)
                normalized_events, normalized_citations = self._normalize_search_results(
                    country_code=country_code,
                    search_results=search_results,
                )
                events.extend(normalized_events)
                citations.extend(normalized_citations)

            if not events:
                output = ExternalRiskAgentOutput(
                    risk_events=[],
                    country_scores=[],
                    citations=[],
                    summary="No active external risk events were found for the requested countries.",
                    highest_severity=1,
                    affected_suppliers=[],
                    affected_products=[],
                    limitations=[],
                    data_source="fresh",
                )
                self.storage.write_external_risk_cache(
                    cache_key,
                    {
                        "cachedAt": _utc_now().isoformat(),
                        "output": output.model_dump(mode="json"),
                    },
                )
                self._finish_trace(
                    trace,
                    status=self._trace_status(partial=False),
                    output_payload=output,
                )
                return output

            affected_suppliers = [
                AffectedSupplierRef(
                    supplier_id=supplier.id,
                    supplier_code=supplier.supplier_code,
                    name=supplier.name,
                    country_code=supplier.country_code,
                )
                for supplier in self.catalog_repository.list_suppliers_by_country_codes(country_codes)
            ]
            affected_products = [
                AffectedProductRef(
                    product_id=product.id,
                    sku=product.sku,
                    name=product.name,
                    category=product.category,
                )
                for product in self.catalog_repository.list_products_by_supplier_countries(country_codes)
            ]
            country_scores = self._aggregate_country_scores(country_codes, events)
            citations = dedupe_citations(citations)
            highest_severity = max(event.severity for event in events)
            summary = (
                f"Found {len(events)} external risk event(s) across {len(country_scores)} country scope(s)."
            )
            output = ExternalRiskAgentOutput(
                risk_events=events,
                country_scores=country_scores,
                citations=citations,
                summary=summary,
                highest_severity=highest_severity,
                affected_suppliers=affected_suppliers,
                affected_products=affected_products,
                limitations=[],
                data_source="fresh",
            )
            with self.database.transaction() as connection:
                for event in events:
                    self.risk_repository.upsert_risk_event(event, connection=connection)
                for score in country_scores:
                    self.risk_repository.upsert_country_score(score, connection=connection)
            self.storage.write_external_risk_cache(
                cache_key,
                {
                    "cachedAt": _utc_now().isoformat(),
                    "output": output.model_dump(mode="json"),
                },
            )
            self._finish_trace(
                trace,
                status=self._trace_status(partial=False),
                output_payload=output,
            )
            return output
        except Exception as exc:
            output = self._cached_or_empty_output(
                cached_output=cached_output,
                cache_is_fresh=cache_is_fresh,
                limitation=f"Live search failed; returned cached results if available. Error: {exc}",
            )
            status = AgentRunStatus.PARTIAL if output.data_source != "empty" else AgentRunStatus.FAILED
            self._finish_trace(
                trace,
                status=status,
                output_payload=output,
                error_message=str(exc),
            )
            return output

    def _collect_country_codes(self, input_model: ExternalRiskAgentInput) -> list[str]:
        values = {
            code.strip().upper()
            for code in (input_model.country_codes + input_model.supplier_countries)
            if code.strip()
        }
        return sorted(values)

    def _build_cache_key(
        self,
        input_model: ExternalRiskAgentInput,
        country_codes: list[str],
    ) -> str:
        key_payload = {
            "countryCodes": country_codes,
            "routeHints": sorted(input_model.route_hints),
            "productCategory": input_model.product_category,
        }
        return json.dumps(key_payload, sort_keys=True)

    def _is_cache_fresh(self, cache_path: Path, freshness_policy_hours: int) -> bool:
        if not cache_path.exists():
            return False
        cache_updated_at = datetime.fromtimestamp(cache_path.stat().st_mtime, tz=timezone.utc)
        if self.settings.external_risk_cache_same_day_only:
            return cache_updated_at.date() == _utc_now().date()
        age = _utc_now() - cache_updated_at
        return age <= timedelta(hours=freshness_policy_hours)

    def _read_cached_output(self, cache_key: str) -> ExternalRiskAgentOutput | None:
        cached_payload = self.storage.read_external_risk_cache(cache_key)
        if not cached_payload:
            return None
        if "output" in cached_payload:
            return ExternalRiskAgentOutput.model_validate(cached_payload["output"])
        return ExternalRiskAgentOutput.model_validate(cached_payload)

    def _cached_or_empty_output(
        self,
        *,
        cached_output: ExternalRiskAgentOutput | None,
        cache_is_fresh: bool,
        limitation: str,
    ) -> ExternalRiskAgentOutput:
        if cached_output is not None:
            limitations = list(cached_output.limitations)
            limitations.append(limitation)
            if not cache_is_fresh:
                limitations.append("Cached external risk data is stale.")
            return cached_output.model_copy(
                update={
                    "limitations": limitations,
                    "data_source": "cached",
                }
            )
        return ExternalRiskAgentOutput(
            risk_events=[],
            country_scores=[],
            citations=[],
            summary="External search is unavailable and no cached external risk data exists yet.",
            highest_severity=1,
            affected_suppliers=[],
            affected_products=[],
            limitations=[limitation, "No cached external risk data exists yet."],
            data_source="empty",
        )

    def _build_search_query(
        self,
        *,
        country_code: str,
        route_hints: list[str],
        product_category: str | None,
    ) -> str:
        resolved_country_name = country_name(country_code)
        route_terms = [hint.strip() for hint in route_hints if hint.strip()]
        focus_terms = [
            "shipping delays",
            "port closures",
            "factory slowdowns",
            "labor strikes",
            "weather disruption",
            "trade restrictions",
            *country_search_focus(country_code),
            *route_terms,
        ]
        deduped_focus_terms = list(dict.fromkeys(focus_terms))
        category_text = f" for {product_category} supply chains" if product_category else ""
        focus_text = ", ".join(deduped_focus_terms)
        return (
            f"Recent cited news about logistics, labor, weather, tariff, or geopolitical disruptions affecting "
            f"{resolved_country_name} ({country_code}){category_text}. "
            f"Prioritize shipment delays, port congestion, factory shutdowns, export constraints, and supplier risk. "
            f"Focus on {focus_text}."
        )

    def _normalize_search_results(
        self,
        *,
        country_code: str,
        search_results: list[dict[str, Any]],
    ) -> tuple[list[ExternalRiskEvent], list[Citation]]:
        detected_at = _utc_now().isoformat()
        events: list[ExternalRiskEvent] = []
        citations: list[Citation] = []
        for result in search_results:
            title = str(result.get("title") or "").strip()
            if not title:
                continue
            source_url = str(result.get("url") or "").strip() or None
            source_name = (
                str(result.get("source_name") or result.get("sourceName") or result.get("publisher") or "").strip()
                or None
            )
            snippet = str(result.get("snippet") or result.get("summary") or "").strip() or None
            risk_type = self._infer_risk_type(result)
            severity = self._infer_severity(result)
            citation = normalize_citation(
                title=title,
                url=source_url,
                source_name=source_name,
                snippet=snippet,
            )
            if citation is not None:
                citations.append(citation)

            event_id = self._event_id(country_code, title, source_url or snippet or detected_at)
            events.append(
                ExternalRiskEvent(
                    event_id=event_id,
                    source_type="search",
                    risk_type=risk_type,
                    severity=severity,
                    title=title,
                    summary=snippet or title,
                    country_code=str(result.get("country_code") or country_code).upper(),
                    route_code=str(result.get("route_code") or "").strip() or None,
                    affected_supplier_id=None,
                    affected_product_id=None,
                    event_date=str(result.get("event_date") or result.get("published_at") or "").strip() or None,
                    detected_at=detected_at,
                    expires_at=None,
                    status="open",
                    source_url=source_url,
                    source_name=source_name,
                    citation_snippet=snippet,
                    confidence=float(result["confidence"]) if "confidence" in result else self._infer_confidence(severity),
                    payload_json=json.dumps(result, sort_keys=True),
                )
            )
        return events, citations

    def _infer_risk_type(self, result: dict[str, Any]) -> str:
        explicit_risk_type = str(result.get("risk_type") or "").strip().lower()
        if explicit_risk_type in RISK_TYPES:
            return explicit_risk_type

        haystack = " ".join(
            str(value).lower()
            for value in (
                result.get("title"),
                result.get("snippet"),
                result.get("summary"),
            )
            if value
        )
        if any(keyword in haystack for keyword in ("tariff", "duty", "trade barrier")):
            return "tariff"
        if any(
            keyword in haystack
            for keyword in (
                "storm",
                "flood",
                "weather",
                "typhoon",
                "earthquake",
                "heatwave",
                "heat wave",
                "extreme heat",
                "drought",
                "wildfire",
            )
        ):
            return "weather"
        if any(keyword in haystack for keyword in ("strike", "labor", "union", "work stoppage")):
            return "labor"
        if any(keyword in haystack for keyword in ("port", "shipping", "delay", "logistics", "route")):
            return "logistics"
        return "geopolitical"

    def _infer_severity(self, result: dict[str, Any]) -> int:
        if "severity" in result:
            try:
                severity = int(result["severity"])
                return max(1, min(5, severity))
            except (TypeError, ValueError):
                pass

        haystack = " ".join(
            str(value).lower()
            for value in (
                result.get("title"),
                result.get("snippet"),
                result.get("summary"),
            )
            if value
        )
        if any(
            keyword in haystack
            for keyword in (
                "shutdown",
                "closed",
                "critical",
                "severe",
                "conflict",
                "blockade",
                "halted",
                "standstill",
                "missile",
                "attack",
            )
        ):
            return 5
        if any(keyword in haystack for keyword in ("major", "strike", "disruption", "backlog", "tariff")):
            return 4
        if any(keyword in haystack for keyword in ("delay", "watch", "warning", "rain", "slowdown")):
            return 3
        return 2

    def _infer_confidence(self, severity: int) -> float:
        return round(min(0.95, 0.55 + (severity * 0.07)), 2)

    def _event_id(self, country_code: str, title: str, unique_source: str) -> str:
        digest = hashlib.sha256(f"{country_code}|{title}|{unique_source}".encode("utf-8")).hexdigest()
        return f"evt_{digest[:16]}"

    def _aggregate_country_scores(
        self,
        country_codes: list[str],
        events: list[ExternalRiskEvent],
    ) -> list[CountryRiskScore]:
        score_date = _utc_now().isoformat()
        scores: list[CountryRiskScore] = []
        for country_code in country_codes:
            country_events = [event for event in events if event.country_code == country_code]
            if not country_events:
                continue
            category_scores = {
                risk_type: max(
                    (event.severity for event in country_events if event.risk_type == risk_type),
                    default=0,
                )
                for risk_type in RISK_TYPES
            }
            non_zero_scores = [score for score in category_scores.values() if score > 0]
            overall_score = clamp(
                average([float(value) for value in non_zero_scores]) + min(0.5, len(country_events) * 0.1),
                minimum=1.0,
                maximum=5.0,
            )
            highest_severity = max(event.severity for event in country_events)
            dominant_categories = [
                risk_type
                for risk_type, score in category_scores.items()
                if score == highest_severity
            ]
            summary = (
                f"{len(country_events)} active event(s); strongest pressure in "
                f"{', '.join(dominant_categories[:2])}."
            )
            scores.append(
                CountryRiskScore(
                    country_code=country_code,
                    score_date=score_date,
                    overall_score=round(overall_score, 2),
                    geopolitical_score=float(category_scores["geopolitical"]),
                    tariff_score=float(category_scores["tariff"]),
                    logistics_score=float(category_scores["logistics"]),
                    weather_score=float(category_scores["weather"]),
                    labor_score=float(category_scores["labor"]),
                    active_event_count=len(country_events),
                    highest_severity=highest_severity,
                    summary=summary,
                )
            )
        return scores
