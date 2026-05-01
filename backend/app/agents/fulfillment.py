from __future__ import annotations

from collections import defaultdict

from app.agents.base import BaseAgent
from app.config import Settings
from app.db.connection import SQLiteConnectionFactory
from app.db.repositories.analytics_repository import AnalyticsRepository
from app.schemas.agents import (
    FulfillmentAgentInput,
    FulfillmentAgentOutput,
    FulfillmentRegionStatus,
)
from app.services.scoring import average, clamp
from app.services.storage import StorageManager


class FulfillmentAgent(BaseAgent):
    def __init__(
        self,
        *,
        settings: Settings,
        storage: StorageManager,
        database: SQLiteConnectionFactory,
    ) -> None:
        super().__init__(
            agent_name="Fulfillment Agent",
            settings=settings,
            storage=storage,
            database=database,
        )
        self.analytics_repository = AnalyticsRepository(database)

    def run(self, input_model: FulfillmentAgentInput) -> FulfillmentAgentOutput:
        trace = self._start_trace(
            trigger_type=input_model.trigger_type,
            trigger_ref=input_model.trigger_ref,
            input_payload=input_model,
        )

        snapshots = self.analytics_repository.list_latest_fulfillment_snapshots(
            product_ids=input_model.product_ids or None,
            region_codes=input_model.region_codes or None,
        )
        if not snapshots:
            output = FulfillmentAgentOutput(
                regional_status=[],
                backlog_orders=0,
                avg_ship_delay_hours=0.0,
                on_time_rate=0.0,
                fulfillment_risk_score=1.0,
                sla_risk_level=1,
                recommended_action="Import fulfillment snapshots before using fulfillment analysis.",
                supporting_notes=["No fulfillment snapshots found for the requested scope."],
                partial=True,
            )
            self._finish_trace(
                trace,
                status=self._trace_status(partial=True),
                output_payload=output,
            )
            return output

        grouped_rows: dict[str, list[dict[str, object]]] = defaultdict(list)
        for row in snapshots:
            grouped_rows[str(row["region_code"])].append(row)

        regional_status: list[FulfillmentRegionStatus] = []
        for region_code, rows in sorted(grouped_rows.items()):
            regional_status.append(
                FulfillmentRegionStatus(
                    region_code=region_code,
                    backlog_orders=sum(int(row["backlog_orders"]) for row in rows),
                    avg_ship_delay_hours=round(
                        average([float(row["avg_ship_delay_hours"]) for row in rows]),
                        2,
                    ),
                    on_time_rate=round(
                        average([float(row["on_time_rate"]) for row in rows]),
                        4,
                    ),
                    sla_risk_level=max(int(row["sla_risk_level"]) for row in rows),
                    warehouse_count=len({row["warehouse_code"] for row in rows}),
                )
            )

        backlog_orders = sum(region.backlog_orders for region in regional_status)
        avg_ship_delay_hours = round(
            average([region.avg_ship_delay_hours for region in regional_status]),
            2,
        )
        on_time_rate = round(
            average([region.on_time_rate for region in regional_status]),
            4,
        )

        external_highest_severity = max(
            (event.severity for event in input_model.external_risk_events),
            default=0,
        )
        supporting_notes: list[str] = []
        if not input_model.external_risk_events:
            supporting_notes.append(
                "External risk context was not provided, so fulfillment risk reflects only local warehouse metrics."
            )

        risk_score = 1.0
        if backlog_orders >= 50:
            risk_score += 1.4
        elif backlog_orders >= 20:
            risk_score += 0.9
        elif backlog_orders > 0:
            risk_score += 0.4

        if avg_ship_delay_hours >= 24:
            risk_score += 1.4
        elif avg_ship_delay_hours >= 12:
            risk_score += 0.9
        elif avg_ship_delay_hours >= 6:
            risk_score += 0.4

        if on_time_rate < 0.85:
            risk_score += 1.4
        elif on_time_rate < 0.92:
            risk_score += 0.9
        elif on_time_rate < 0.96:
            risk_score += 0.4

        if external_highest_severity >= 4:
            risk_score += 0.7
            supporting_notes.append(
                "External risk context includes high-severity disruptions that may worsen SLA performance."
            )
        elif external_highest_severity >= 3:
            risk_score += 0.4

        fulfillment_risk_score = round(clamp(risk_score), 2)
        sla_risk_level = max(
            max(region.sla_risk_level for region in regional_status),
            int(round(fulfillment_risk_score)),
        )
        sla_risk_level = max(1, min(5, sla_risk_level))

        if fulfillment_risk_score >= 4.2:
            recommended_action = "Escalate backlog recovery and re-route constrained orders immediately."
        elif fulfillment_risk_score >= 3.2:
            recommended_action = "Prioritize delayed regions and confirm carrier or warehouse recovery actions."
        elif fulfillment_risk_score >= 2.3:
            recommended_action = "Monitor regional backlog and review SLA trends daily."
        else:
            recommended_action = "Fulfillment is stable; continue standard SLA monitoring."

        output = FulfillmentAgentOutput(
            regional_status=regional_status,
            backlog_orders=backlog_orders,
            avg_ship_delay_hours=avg_ship_delay_hours,
            on_time_rate=on_time_rate,
            fulfillment_risk_score=fulfillment_risk_score,
            sla_risk_level=sla_risk_level,
            recommended_action=recommended_action,
            supporting_notes=supporting_notes,
            partial=False,
        )
        self._finish_trace(
            trace,
            status=self._trace_status(partial=False),
            output_payload=output,
        )
        return output
