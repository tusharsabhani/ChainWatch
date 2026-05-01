from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone

from app.agents.base import BaseAgent
from app.config import Settings
from app.db.connection import SQLiteConnectionFactory
from app.db.repositories.analytics_repository import AnalyticsRepository
from app.schemas.agents import (
    AgentTriggerType,
    DemandAgentInput,
    DemandAgentOutput,
    HistoricalTrendPoint,
    RecentSpike,
    SeasonalWindow,
)
from app.services.scoring import average, clamp
from app.services.storage import StorageManager


def _month_start(value: str) -> str:
    parsed_date = datetime.fromisoformat(value.replace("Z", "+00:00")).date() if "T" in value else date.fromisoformat(value)
    return parsed_date.replace(day=1).isoformat()


class DemandAgent(BaseAgent):
    def __init__(
        self,
        *,
        settings: Settings,
        storage: StorageManager,
        database: SQLiteConnectionFactory,
    ) -> None:
        super().__init__(
            agent_name="Demand Agent",
            settings=settings,
            storage=storage,
            database=database,
        )
        self.analytics_repository = AnalyticsRepository(database)

    def run(self, input_model: DemandAgentInput) -> DemandAgentOutput:
        trace = self._start_trace(
            trigger_type=input_model.trigger_type,
            trigger_ref=input_model.trigger_ref,
            input_payload=input_model,
        )

        sales_rows = self.analytics_repository.list_sales_history_rows(
            product_ids=input_model.product_ids,
            region_filter=input_model.region_filter,
            channel_filter=input_model.channel_filter,
        )

        if not sales_rows:
            output = DemandAgentOutput(
                historical_trend=[],
                seasonal_windows=[],
                recent_spikes=[],
                forecast_window_days=input_model.forecast_window_days,
                forecasted_units=0,
                demand_risk_score=1.0,
                supporting_notes=["No sales history found for the requested scope."],
                low_confidence=True,
            )
            self._finish_trace(
                trace,
                status=self._trace_status(partial=True),
                output_payload=output,
            )
            return output

        monthly_buckets: dict[str, dict[str, float]] = defaultdict(
            lambda: {
                "units_sold": 0,
                "net_revenue": 0.0,
                "returns_qty": 0,
                "promo_periods": 0,
                "stockout_periods": 0,
            }
        )
        dates: list[date] = []
        for row in sales_rows:
            period_start = _month_start(str(row["sales_date"]))
            bucket = monthly_buckets[period_start]
            bucket["units_sold"] += int(row["units_sold"])
            bucket["net_revenue"] += float(row["net_revenue"])
            bucket["returns_qty"] += int(row["returns_qty"])
            bucket["promo_periods"] += int(row["promo_flag"])
            bucket["stockout_periods"] += int(row["stockout_flag"])
            sales_date = (
                datetime.fromisoformat(str(row["sales_date"]).replace("Z", "+00:00")).date()
                if "T" in str(row["sales_date"])
                else date.fromisoformat(str(row["sales_date"]))
            )
            dates.append(sales_date)

        historical_trend = [
            HistoricalTrendPoint(
                period_start=period_start,
                units_sold=int(bucket["units_sold"]),
                net_revenue=round(float(bucket["net_revenue"]), 2),
                returns_qty=int(bucket["returns_qty"]),
                promo_periods=int(bucket["promo_periods"]),
                stockout_periods=int(bucket["stockout_periods"]),
            )
            for period_start, bucket in sorted(monthly_buckets.items())
        ]

        monthly_averages: dict[int, list[int]] = defaultdict(list)
        for point in historical_trend:
            month_number = date.fromisoformat(point.period_start).month
            monthly_averages[month_number].append(point.units_sold)

        overall_avg_units = average([float(point.units_sold) for point in historical_trend]) or 1.0
        seasonal_windows: list[SeasonalWindow] = []
        for month_number in sorted(monthly_averages.keys()):
            avg_units = average([float(value) for value in monthly_averages[month_number]])
            if avg_units >= overall_avg_units * 1.15:
                label = "peak"
            elif avg_units <= overall_avg_units * 0.85:
                label = "soft"
            else:
                continue
            seasonal_windows.append(
                SeasonalWindow(
                    start_month=month_number,
                    end_month=month_number,
                    avg_units=round(avg_units, 2),
                    label=label,
                )
            )

        recent_spikes: list[RecentSpike] = []
        for index in range(max(3, len(historical_trend) - 6), len(historical_trend)):
            current_point = historical_trend[index]
            baseline_points = historical_trend[max(0, index - 6):index]
            if len(baseline_points) < 3:
                continue
            baseline_units = average([float(point.units_sold) for point in baseline_points])
            if baseline_units <= 0:
                continue
            spike_ratio = current_point.units_sold / baseline_units
            if spike_ratio >= 1.25 and current_point.units_sold - baseline_units >= 5:
                recent_spikes.append(
                    RecentSpike(
                        period_start=current_point.period_start,
                        units_sold=current_point.units_sold,
                        baseline_units=round(baseline_units, 2),
                        spike_ratio=round(spike_ratio, 2),
                        reason="Recent demand moved materially above the trailing six-month baseline.",
                    )
                )

        recent_points = historical_trend[-3:] if len(historical_trend) >= 3 else historical_trend
        recent_average_units = average([float(point.units_sold) for point in recent_points])
        forecasted_units = int(round((recent_average_units / 30.0) * input_model.forecast_window_days))

        history_span_days = (max(dates) - min(dates)).days if len(dates) > 1 else 0
        low_confidence = history_span_days < 365 or len(historical_trend) < 12

        current_month = datetime.now(timezone.utc).month
        current_month_window = next(
            (window for window in seasonal_windows if window.start_month == current_month and window.label == "peak"),
            None,
        )
        recent_stockout_periods = sum(point.stockout_periods for point in historical_trend[-3:])
        recent_promo_periods = sum(point.promo_periods for point in historical_trend[-3:])

        risk_score = 1.0
        risk_score += min(1.5, len(recent_spikes) * 0.45)
        risk_score += 0.8 if recent_stockout_periods > 0 else 0.0
        risk_score += 0.6 if recent_promo_periods > 0 else 0.0
        risk_score += 0.7 if current_month_window is not None else 0.0
        risk_score += 0.3 if recent_average_units > overall_avg_units * 1.1 else 0.0
        if low_confidence:
            risk_score = max(1.0, risk_score - 0.2)

        supporting_notes: list[str] = []
        if low_confidence:
            supporting_notes.append(
                "Sales history is below 12 months, so this demand result is low-confidence."
            )
        if recent_spikes:
            supporting_notes.append(
                f"Detected {len(recent_spikes)} recent spike period(s) in the trailing months."
            )
        if current_month_window is not None:
            supporting_notes.append(
                "The current month falls inside a high-season demand window."
            )
        if recent_stockout_periods > 0:
            supporting_notes.append(
                "Recent stockout flags indicate demand pressure may be understated by lost availability."
            )
        if not supporting_notes:
            supporting_notes.append(
                "Demand has been relatively steady across the available history."
            )

        output = DemandAgentOutput(
            historical_trend=historical_trend,
            seasonal_windows=seasonal_windows,
            recent_spikes=recent_spikes,
            forecast_window_days=input_model.forecast_window_days,
            forecasted_units=max(0, forecasted_units),
            demand_risk_score=round(clamp(risk_score), 2),
            supporting_notes=supporting_notes,
            low_confidence=low_confidence,
        )
        self._finish_trace(
            trace,
            status=self._trace_status(partial=low_confidence),
            output_payload=output,
        )
        return output
