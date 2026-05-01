from __future__ import annotations

import sqlite3
from collections.abc import Sequence

from app.db.repositories.base import SQLiteRepository
from app.schemas.agents import CountryRiskScore, ExternalRiskEvent


def _placeholders(items: Sequence[object]) -> str:
    return ", ".join("?" for _ in items)


class RiskRepository(SQLiteRepository):
    def upsert_risk_event(
        self,
        event: ExternalRiskEvent,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self.execute(
            """
            INSERT INTO risk_events (
                id,
                source_type,
                risk_type,
                severity,
                title,
                summary,
                country_code,
                route_code,
                affected_supplier_id,
                affected_product_id,
                event_date,
                detected_at,
                expires_at,
                status,
                source_url,
                source_name,
                citation_snippet,
                confidence,
                payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                source_type = excluded.source_type,
                risk_type = excluded.risk_type,
                severity = excluded.severity,
                title = excluded.title,
                summary = excluded.summary,
                country_code = excluded.country_code,
                route_code = excluded.route_code,
                affected_supplier_id = excluded.affected_supplier_id,
                affected_product_id = excluded.affected_product_id,
                event_date = excluded.event_date,
                detected_at = excluded.detected_at,
                expires_at = excluded.expires_at,
                status = excluded.status,
                source_url = excluded.source_url,
                source_name = excluded.source_name,
                citation_snippet = excluded.citation_snippet,
                confidence = excluded.confidence,
                payload_json = excluded.payload_json
            """,
            (
                event.event_id,
                event.source_type,
                event.risk_type,
                event.severity,
                event.title,
                event.summary,
                event.country_code,
                event.route_code,
                event.affected_supplier_id,
                event.affected_product_id,
                event.event_date,
                event.detected_at,
                event.expires_at,
                event.status,
                event.source_url,
                event.source_name,
                event.citation_snippet,
                event.confidence,
                event.payload_json,
            ),
            connection=connection,
        )

    def upsert_country_score(
        self,
        score: CountryRiskScore,
        *,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self.execute(
            """
            INSERT INTO country_risk_scores (
                country_code,
                score_date,
                overall_score,
                geopolitical_score,
                tariff_score,
                logistics_score,
                weather_score,
                labor_score,
                active_event_count,
                highest_severity,
                summary
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(country_code, score_date) DO UPDATE SET
                overall_score = excluded.overall_score,
                geopolitical_score = excluded.geopolitical_score,
                tariff_score = excluded.tariff_score,
                logistics_score = excluded.logistics_score,
                weather_score = excluded.weather_score,
                labor_score = excluded.labor_score,
                active_event_count = excluded.active_event_count,
                highest_severity = excluded.highest_severity,
                summary = excluded.summary
            """,
            (
                score.country_code,
                score.score_date,
                score.overall_score,
                score.geopolitical_score,
                score.tariff_score,
                score.logistics_score,
                score.weather_score,
                score.labor_score,
                score.active_event_count,
                score.highest_severity,
                score.summary,
            ),
            connection=connection,
        )

    def list_active_risk_events_by_country_codes(self, country_codes: list[str]) -> list[dict[str, object]]:
        if not country_codes:
            return []
        rows = self.fetch_all(
            f"""
            SELECT *
            FROM risk_events
            WHERE country_code IN ({_placeholders(country_codes)})
              AND status IN ('open', 'monitoring')
            ORDER BY severity DESC, detected_at DESC
            """,
            country_codes,
        )
        return [dict(row) for row in rows]

    def list_latest_country_scores(self, country_codes: list[str]) -> list[dict[str, object]]:
        if not country_codes:
            return []
        rows = self.fetch_all(
            f"""
            SELECT score.*
            FROM country_risk_scores AS score
            INNER JOIN (
                SELECT
                    country_code,
                    MAX(score_date) AS latest_score_date
                FROM country_risk_scores
                WHERE country_code IN ({_placeholders(country_codes)})
                GROUP BY country_code
            ) latest
                ON latest.country_code = score.country_code
               AND latest.latest_score_date = score.score_date
            ORDER BY score.country_code ASC
            """,
            country_codes,
        )
        return [dict(row) for row in rows]
