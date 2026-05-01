from __future__ import annotations

from app.agents.base import BaseAgent
from app.config import Settings
from app.db.connection import SQLiteConnectionFactory
from app.db.repositories.analytics_repository import AnalyticsRepository
from app.schemas.agents import InventoryAgentInput, InventoryAgentOutput
from app.services.scoring import average, clamp
from app.services.storage import StorageManager


class InventoryAgent(BaseAgent):
    def __init__(
        self,
        *,
        settings: Settings,
        storage: StorageManager,
        database: SQLiteConnectionFactory,
    ) -> None:
        super().__init__(
            agent_name="Inventory Agent",
            settings=settings,
            storage=storage,
            database=database,
        )
        self.analytics_repository = AnalyticsRepository(database)

    def run(self, input_model: InventoryAgentInput) -> InventoryAgentOutput:
        trace = self._start_trace(
            trigger_type=input_model.trigger_type,
            trigger_ref=input_model.trigger_ref,
            input_payload=input_model,
        )

        snapshots = self.analytics_repository.list_latest_inventory_snapshots(
            product_ids=input_model.product_ids,
        )
        if not snapshots:
            output = InventoryAgentOutput(
                current_on_hand=0,
                reserved_qty=0,
                inbound_qty=0,
                days_of_cover=None,
                reorder_point=0,
                stockout_risk_score=1.0,
                inventory_status="no_data",
                recommended_action="Import inventory snapshots before using inventory analysis.",
                supporting_notes=["No inventory snapshots found for the requested scope."],
                partial=True,
            )
            self._finish_trace(
                trace,
                status=self._trace_status(partial=True),
                output_payload=output,
            )
            return output

        current_on_hand = sum(int(row["on_hand_qty"]) for row in snapshots)
        reserved_qty = sum(int(row["reserved_qty"]) for row in snapshots)
        inbound_qty = sum(int(row["inbound_qty"]) for row in snapshots)
        reorder_point = sum(int(row["reorder_point"]) for row in snapshots)
        safety_stock = sum(int(row["safety_stock"]) for row in snapshots)
        available_qty = max(0, current_on_hand - reserved_qty)

        snapshot_days_of_cover_values = [
            float(row["days_of_cover"])
            for row in snapshots
            if row["days_of_cover"] is not None
        ]
        days_of_cover = (
            round(average(snapshot_days_of_cover_values), 2)
            if snapshot_days_of_cover_values
            else None
        )

        supporting_notes: list[str] = []
        partial = False

        if days_of_cover is None and input_model.demand_signals:
            daily_forecast_units = sum(
                signal.forecasted_units / max(signal.forecast_window_days, 1)
                for signal in input_model.demand_signals
            )
            if daily_forecast_units > 0:
                days_of_cover = round(available_qty / daily_forecast_units, 2)
                supporting_notes.append(
                    "Days of cover was estimated from the demand forecast because snapshots did not include it."
                )

        if not input_model.demand_signals:
            partial = True
            supporting_notes.append(
                "Demand signals were not provided, so inventory risk used static thresholds."
            )

        risk_score = 1.0
        coverage_ratio = available_qty / max(reorder_point, 1) if reorder_point > 0 else 1.5
        if available_qty <= 0:
            risk_score += 2.3
        elif coverage_ratio < 0.5:
            risk_score += 1.9
        elif coverage_ratio < 1.0:
            risk_score += 1.3
        elif coverage_ratio < 1.3:
            risk_score += 0.6

        if available_qty < safety_stock:
            risk_score += 0.9

        if days_of_cover is not None:
            if days_of_cover < 7:
                risk_score += 1.2
            elif days_of_cover < 14:
                risk_score += 0.7
            elif days_of_cover < 21:
                risk_score += 0.3
        else:
            partial = True
            supporting_notes.append(
                "Days of cover could not be calculated from available inventory or demand data."
            )

        if inbound_qty == 0:
            risk_score += 0.4
            supporting_notes.append(
                "No inbound quantity is currently recorded for this scope."
            )

        if input_model.demand_signals:
            average_demand_risk = average(
                [signal.demand_risk_score for signal in input_model.demand_signals]
            )
            risk_score += max(0.0, (average_demand_risk - 2.0) / 3.0)

        stockout_risk_score = round(clamp(risk_score), 2)
        if stockout_risk_score >= 4.2:
            inventory_status = "critical"
            recommended_action = "Replenish immediately and review substitute supply options."
        elif stockout_risk_score >= 3.2:
            inventory_status = "reorder"
            recommended_action = "Create a replenishment action within the next few days."
        elif stockout_risk_score >= 2.3:
            inventory_status = "watch"
            recommended_action = "Monitor inventory closely and confirm inbound timing."
        else:
            inventory_status = "healthy"
            recommended_action = "Inventory is currently healthy; continue routine monitoring."

        output = InventoryAgentOutput(
            current_on_hand=current_on_hand,
            reserved_qty=reserved_qty,
            inbound_qty=inbound_qty,
            days_of_cover=days_of_cover,
            reorder_point=reorder_point,
            stockout_risk_score=stockout_risk_score,
            inventory_status=inventory_status,
            recommended_action=recommended_action,
            supporting_notes=supporting_notes,
            partial=partial,
        )
        self._finish_trace(
            trace,
            status=self._trace_status(partial=partial),
            output_payload=output,
        )
        return output
