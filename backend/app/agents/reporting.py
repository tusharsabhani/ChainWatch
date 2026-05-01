from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
import uuid

from app.adapters.search import NullSearchAdapter, SearchAdapter
from app.agents.base import BaseAgent
from app.agents.demand import DemandAgent
from app.agents.external_risk import ExternalRiskAgent
from app.agents.fulfillment import FulfillmentAgent
from app.agents.inventory import InventoryAgent
from app.config import Settings
from app.db.connection import SQLiteConnectionFactory
from app.db.repositories.catalog_repository import CatalogRepository
from app.db.repositories.chat_repository import ChatRepository
from app.db.repositories.report_repository import ReportRepository
from app.schemas.agents import AgentRunStatus, AgentTriggerType, Citation, DemandSignal
from app.schemas.chat import ChatMessageRole
from app.schemas.reports import (
    GeneratedReportArtifact,
    ReportArtifactPaths,
    ReportGenerationResult,
    ReportRecord,
    ReportRequest,
    ReportScopeType,
    ReportSection,
    ReportStatus,
    ReportingAgentInput,
    ReportingAgentOutput,
)
from app.services.citations import dedupe_citations
from app.services.storage import StorageManager


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class _ResolvedScope:
    title_suffix: str
    product_ids: list[int]
    country_codes: list[str]
    scope_label: str


class ReportingAgent(BaseAgent):
    def __init__(
        self,
        *,
        settings: Settings,
        storage: StorageManager,
        database: SQLiteConnectionFactory,
        search_adapter: SearchAdapter | None = None,
    ) -> None:
        super().__init__(
            agent_name="Reporting Agent",
            settings=settings,
            storage=storage,
            database=database,
        )
        self.catalog_repository = CatalogRepository(database)
        self.chat_repository = ChatRepository(database)
        self.report_repository = ReportRepository(database)
        self.search_adapter = search_adapter or NullSearchAdapter()

    def run(self, input_model: ReportingAgentInput) -> ReportingAgentOutput:
        trace = self._start_trace(
            trigger_type=AgentTriggerType.REPORT,
            trigger_ref=input_model.report_id,
            input_payload=input_model,
        )
        self.report_repository.mark_running(input_model.report_id)

        json_path = self.storage.report_json_path(input_model.report_id)
        markdown_path = self.storage.report_markdown_path(input_model.report_id)

        try:
            resolved_scope = self._resolve_scope(input_model)
            sections, used_agents = self._build_sections(
                input_model=input_model,
                resolved_scope=resolved_scope,
            )

            citations = dedupe_citations(
                [citation for section in sections for citation in section.citations]
            )
            limitations = []
            for section in sections:
                limitations.extend(section.limitations)
            limitations = list(dict.fromkeys(limitations))

            generation_status = (
                ReportStatus.PARTIAL
                if any(section.status != AgentRunStatus.COMPLETED for section in sections) or limitations
                else ReportStatus.COMPLETED
            )
            summary = self._build_summary(
                title=input_model.title,
                sections=sections,
                limitations=limitations,
            )

            artifact = GeneratedReportArtifact(
                report_id=input_model.report_id,
                report_type=input_model.report_type,
                scope_type=input_model.scope_type,
                scope_id=input_model.scope_id,
                title=input_model.title,
                generated_at=_utc_now_iso(),
                status=generation_status,
                summary=summary,
                limitations=limitations,
                citations=citations,
                used_agents=used_agents,
                sections=sections,
                artifact_paths=ReportArtifactPaths(
                    json_path=self.settings.to_relative_path(json_path),
                    markdown_path=self.settings.to_relative_path(markdown_path),
                ),
            )
            self.storage.write_json_artifact(json_path, artifact.model_dump(mode="json"))

            markdown_output: str | None = None
            error_message: str | None = None
            markdown_relative_path: str | None = self.settings.to_relative_path(markdown_path)
            try:
                markdown_output = self._render_markdown(artifact)
                self.storage.write_markdown_artifact(markdown_path, markdown_output)
            except Exception as exc:
                generation_status = ReportStatus.PARTIAL
                markdown_relative_path = None
                error_message = f"Markdown rendering failed: {exc}"
                artifact = artifact.model_copy(
                    update={
                        "status": generation_status,
                        "artifact_paths": ReportArtifactPaths(
                            json_path=self.settings.to_relative_path(json_path),
                            markdown_path=None,
                        ),
                        "limitations": list(dict.fromkeys([*artifact.limitations, error_message])),
                    }
                )
                self.storage.write_json_artifact(json_path, artifact.model_dump(mode="json"))

            report_record = self.report_repository.finalize_report(
                report_id=input_model.report_id,
                status=generation_status,
                json_path=self.settings.to_relative_path(json_path),
                markdown_path=markdown_relative_path,
                summary=summary,
                error_message=error_message or (
                    "; ".join(limitations)[:500] if generation_status == ReportStatus.PARTIAL and limitations else None
                ),
            )
            output = ReportingAgentOutput(
                report_json=artifact.model_dump(mode="json"),
                report_markdown=markdown_output,
                summary=summary,
                artifact_paths=ReportArtifactPaths(
                    json_path=report_record.json_path,
                    markdown_path=report_record.markdown_path,
                ),
                generation_status=report_record.status,
                limitations=limitations,
            )
            self._finish_trace(
                trace,
                status=self._report_status_to_run_status(report_record.status),
                output_payload=output,
                error_message=report_record.error_message,
            )
            return output
        except Exception as exc:
            report_record = self.report_repository.finalize_report(
                report_id=input_model.report_id,
                status=ReportStatus.FAILED,
                json_path=None,
                markdown_path=None,
                summary=None,
                error_message=str(exc),
            )
            output = ReportingAgentOutput(
                report_json={},
                report_markdown=None,
                summary=report_record.summary or "Report generation failed.",
                artifact_paths=ReportArtifactPaths(),
                generation_status=ReportStatus.FAILED,
                limitations=[str(exc)],
            )
            self._finish_trace(
                trace,
                status=AgentRunStatus.FAILED,
                output_payload=output,
                error_message=str(exc),
            )
            return output

    def _resolve_scope(self, input_model: ReportingAgentInput) -> _ResolvedScope:
        if input_model.scope_type == ReportScopeType.DASHBOARD:
            return _ResolvedScope(
                title_suffix="Dashboard",
                product_ids=self.catalog_repository.list_all_product_ids(),
                country_codes=self.catalog_repository.list_all_supplier_country_codes(),
                scope_label="dashboard",
            )

        if input_model.scope_type == ReportScopeType.PRODUCT:
            if input_model.scope_id is None:
                raise ValueError("Product reports require a scope_id.")
            product = self.catalog_repository.get_product_by_id(int(input_model.scope_id))
            if product is None:
                raise ValueError(f"Product {input_model.scope_id} was not found.")
            return _ResolvedScope(
                title_suffix=product.name,
                product_ids=[product.id],
                country_codes=self.catalog_repository.list_supplier_country_codes_for_product_ids([product.id]),
                scope_label=f"product {product.sku}",
            )

        if input_model.scope_type == ReportScopeType.COUNTRY:
            if input_model.scope_id is None:
                raise ValueError("Country reports require a scope_id.")
            country_code = input_model.scope_id.strip().upper()
            if not country_code:
                raise ValueError("Country reports require a non-empty country code.")
            return _ResolvedScope(
                title_suffix=country_code,
                product_ids=[],
                country_codes=[country_code],
                scope_label=f"country {country_code}",
            )

        if input_model.scope_type == ReportScopeType.SUPPLIER:
            if input_model.scope_id is None:
                raise ValueError("Supplier reports require a scope_id.")
            supplier = self.catalog_repository.get_supplier_by_id(int(input_model.scope_id))
            if supplier is None:
                raise ValueError(f"Supplier {input_model.scope_id} was not found.")
            return _ResolvedScope(
                title_suffix=supplier.name,
                product_ids=[],
                country_codes=[supplier.country_code],
                scope_label=f"supplier {supplier.supplier_code}",
            )

        if input_model.scope_type == ReportScopeType.CHAT:
            return _ResolvedScope(
                title_suffix=input_model.scope_id or "chat",
                product_ids=[],
                country_codes=[],
                scope_label=f"chat {input_model.scope_id or 'session'}",
            )

        raise ValueError(f"Unsupported report scope: {input_model.scope_type}")

    def _build_sections(
        self,
        *,
        input_model: ReportingAgentInput,
        resolved_scope: _ResolvedScope,
    ) -> tuple[list[ReportSection], list[str]]:
        if input_model.scope_type == ReportScopeType.CHAT:
            return self._build_chat_sections(input_model)

        demand_agent = DemandAgent(
            settings=self.settings,
            storage=self.storage,
            database=self.database,
        )
        inventory_agent = InventoryAgent(
            settings=self.settings,
            storage=self.storage,
            database=self.database,
        )
        fulfillment_agent = FulfillmentAgent(
            settings=self.settings,
            storage=self.storage,
            database=self.database,
        )
        external_risk_agent = ExternalRiskAgent(
            settings=self.settings,
            storage=self.storage,
            database=self.database,
            search_adapter=self.search_adapter,
        )

        sections: list[ReportSection] = []
        used_agents: list[str] = []

        demand_output = None
        if resolved_scope.product_ids:
            demand_output = demand_agent.run(
                input_model=self._build_demand_input(
                    product_ids=resolved_scope.product_ids,
                    trigger_ref=input_model.report_id,
                )
            )
            used_agents.append("Demand Agent")
            sections.append(
                ReportSection(
                    section_id="demand",
                    title="Demand",
                    status=AgentRunStatus.PARTIAL if demand_output.low_confidence else AgentRunStatus.COMPLETED,
                    summary=(
                        f"Forecasted demand over the next {demand_output.forecast_window_days} days is "
                        f"{demand_output.forecasted_units} units with risk score {demand_output.demand_risk_score}."
                    ),
                    data=demand_output.model_dump(mode="json"),
                    limitations=demand_output.supporting_notes if demand_output.low_confidence else [],
                )
            )

        external_output = None
        if resolved_scope.country_codes:
            external_output = external_risk_agent.run(
                input_model=self._build_external_input(
                    country_codes=resolved_scope.country_codes,
                    trigger_ref=input_model.report_id,
                    freshness_policy_hours=input_model.freshness_policy_hours,
                )
            )
            used_agents.append("External Risk Agent")
            sections.append(
                ReportSection(
                    section_id="external-risk",
                    title="External Risk",
                    status=self._section_status_from_external_output(external_output),
                    summary=external_output.summary,
                    data=external_output.model_dump(mode="json"),
                    limitations=list(external_output.limitations),
                    citations=external_output.citations,
                )
            )

        if resolved_scope.product_ids:
            demand_signals = (
                [
                    DemandSignal(
                        product_id=resolved_scope.product_ids[0],
                        forecast_window_days=demand_output.forecast_window_days,
                        forecasted_units=demand_output.forecasted_units,
                        demand_risk_score=demand_output.demand_risk_score,
                    )
                ]
                if demand_output is not None and len(resolved_scope.product_ids) == 1
                else []
            )
            inventory_output = inventory_agent.run(
                input_model=self._build_inventory_input(
                    product_ids=resolved_scope.product_ids,
                    demand_signals=demand_signals,
                    trigger_ref=input_model.report_id,
                )
            )
            used_agents.append("Inventory Agent")
            sections.append(
                ReportSection(
                    section_id="inventory",
                    title="Inventory",
                    status=AgentRunStatus.PARTIAL if inventory_output.partial else AgentRunStatus.COMPLETED,
                    summary=(
                        f"Inventory is {inventory_output.inventory_status} with stockout risk "
                        f"{inventory_output.stockout_risk_score} and recommendation: {inventory_output.recommended_action}"
                    ),
                    data=inventory_output.model_dump(mode="json"),
                    limitations=list(inventory_output.supporting_notes),
                )
            )

            fulfillment_output = fulfillment_agent.run(
                input_model=self._build_fulfillment_input(
                    product_ids=resolved_scope.product_ids,
                    external_risk_events=external_output.risk_events if external_output is not None else [],
                    trigger_ref=input_model.report_id,
                )
            )
            used_agents.append("Fulfillment Agent")
            sections.append(
                ReportSection(
                    section_id="fulfillment",
                    title="Fulfillment",
                    status=AgentRunStatus.PARTIAL if fulfillment_output.partial else AgentRunStatus.COMPLETED,
                    summary=(
                        f"Fulfillment risk is {fulfillment_output.fulfillment_risk_score} with "
                        f"on-time rate {round(fulfillment_output.on_time_rate * 100, 1)}%."
                    ),
                    data=fulfillment_output.model_dump(mode="json"),
                    limitations=list(fulfillment_output.supporting_notes),
                )
            )

        return sections, used_agents

    def _build_chat_sections(
        self,
        input_model: ReportingAgentInput,
    ) -> tuple[list[ReportSection], list[str]]:
        if input_model.scope_id is None:
            raise ValueError("Chat export reports require a scope_id.")
        session = self.chat_repository.get_session(input_model.scope_id)
        if session is None:
            raise ValueError(f"Chat session {input_model.scope_id} was not found.")
        messages = self.chat_repository.list_messages(input_model.scope_id)
        limitations: list[str] = []
        if not messages:
            limitations.append("This chat session does not contain any messages yet.")
        if not any(message.role == ChatMessageRole.ASSISTANT for message in messages):
            limitations.append("This chat export does not include any assistant messages yet.")

        section = ReportSection(
            section_id="chat-export",
            title="Chat Transcript",
            status=AgentRunStatus.PARTIAL if limitations else AgentRunStatus.COMPLETED,
            summary=f"Exported {len(messages)} message(s) from chat session {session.title}.",
            data={
                "session": session.model_dump(mode="json"),
                "messages": [message.model_dump(mode="json") for message in messages],
            },
            limitations=limitations,
            citations=dedupe_citations(
                [citation for message in messages for citation in message.citations]
            ),
        )
        return [section], ["Chat Orchestrator"]

    def _build_demand_input(self, *, product_ids: list[int], trigger_ref: str):
        from app.schemas.agents import DemandAgentInput

        return DemandAgentInput(
            product_ids=product_ids,
            trigger_type=AgentTriggerType.REPORT,
            trigger_ref=trigger_ref,
        )

    def _build_inventory_input(self, *, product_ids: list[int], demand_signals: list[DemandSignal], trigger_ref: str):
        from app.schemas.agents import InventoryAgentInput

        return InventoryAgentInput(
            product_ids=product_ids,
            demand_signals=demand_signals,
            trigger_type=AgentTriggerType.REPORT,
            trigger_ref=trigger_ref,
        )

    def _build_fulfillment_input(self, *, product_ids: list[int], external_risk_events: list[Any], trigger_ref: str):
        from app.schemas.agents import FulfillmentAgentInput

        return FulfillmentAgentInput(
            product_ids=product_ids,
            external_risk_events=external_risk_events,
            trigger_type=AgentTriggerType.REPORT,
            trigger_ref=trigger_ref,
        )

    def _build_external_input(self, *, country_codes: list[str], trigger_ref: str, freshness_policy_hours: int):
        from app.schemas.agents import ExternalRiskAgentInput

        return ExternalRiskAgentInput(
            country_codes=country_codes,
            freshness_policy_hours=freshness_policy_hours,
            trigger_type=AgentTriggerType.REPORT,
            trigger_ref=trigger_ref,
        )

    def _build_summary(
        self,
        *,
        title: str,
        sections: list[ReportSection],
        limitations: list[str],
    ) -> str:
        completed_sections = len([section for section in sections if section.status == AgentRunStatus.COMPLETED])
        partial_sections = len([section for section in sections if section.status == AgentRunStatus.PARTIAL])
        if limitations:
            return (
                f"{title} includes {completed_sections} complete section(s) and "
                f"{partial_sections} partial section(s), with {len(limitations)} limitation note(s)."
            )
        return f"{title} completed with {completed_sections} section(s) and no visible data gaps."

    def _render_markdown(self, artifact: GeneratedReportArtifact) -> str:
        lines = [
            f"# {artifact.title}",
            "",
            f"- Report ID: `{artifact.report_id}`",
            f"- Scope: `{artifact.scope_type.value}`",
            f"- Status: `{artifact.status.value}`",
            f"- Generated At: `{artifact.generated_at}`",
            "",
            "## Summary",
            "",
            artifact.summary,
            "",
            "## Limitations",
            "",
        ]
        if artifact.limitations:
            lines.extend(f"- {limitation}" for limitation in artifact.limitations)
        else:
            lines.append("- None.")

        if artifact.citations:
            lines.extend(["", "## Citations", ""])
            for citation in artifact.citations:
                source_suffix = f" ({citation.source_name})" if citation.source_name else ""
                lines.append(f"- [{citation.title}]({citation.url}){source_suffix}")

        for section in artifact.sections:
            lines.extend(
                [
                    "",
                    f"## {section.title}",
                    "",
                    f"Status: `{section.status.value}`",
                    "",
                    section.summary,
                    "",
                ]
            )
            if section.limitations:
                lines.append("Limitations:")
                lines.extend(f"- {limitation}" for limitation in section.limitations)
                lines.append("")
            lines.extend(
                [
                    "```json",
                    self._pretty_json(section.data),
                    "```",
                ]
            )
        return "\n".join(lines).strip() + "\n"

    def _pretty_json(self, payload: dict[str, Any]) -> str:
        import json

        return json.dumps(payload, indent=2, sort_keys=True)

    def _section_status_from_external_output(self, output) -> AgentRunStatus:
        if output.data_source == "fresh" and not output.limitations:
            return AgentRunStatus.COMPLETED
        if output.data_source == "empty" and output.limitations:
            return AgentRunStatus.FAILED
        return AgentRunStatus.PARTIAL

    def _report_status_to_run_status(self, status: ReportStatus) -> AgentRunStatus:
        if status == ReportStatus.COMPLETED:
            return AgentRunStatus.COMPLETED
        if status == ReportStatus.PARTIAL:
            return AgentRunStatus.PARTIAL
        return AgentRunStatus.FAILED


class ReportService:
    def __init__(
        self,
        *,
        settings: Settings,
        storage: StorageManager,
        database: SQLiteConnectionFactory,
        search_adapter: SearchAdapter | None = None,
    ) -> None:
        self.settings = settings
        self.catalog_repository = CatalogRepository(database)
        self.report_repository = ReportRepository(database)
        self.agent = ReportingAgent(
            settings=settings,
            storage=storage,
            database=database,
            search_adapter=search_adapter,
        )

    def generate_report(self, request: ReportRequest) -> ReportGenerationResult:
        report = self.queue_report(request)
        return self.generate_existing_report(report.id)

    def queue_report(self, request: ReportRequest) -> ReportRecord:
        report_id = f"rep_{uuid.uuid4().hex[:12]}"
        title = request.title or self._default_title(request)
        return self.report_repository.create_report(
            report_id=report_id,
            request=request,
            title=title,
        )

    def generate_existing_report(self, report_id: str) -> ReportGenerationResult:
        report = self.report_repository.get_report(report_id)
        if report is None:
            raise RuntimeError(f"Report {report_id} was not found before generation.")
        output = self.agent.run(
            ReportingAgentInput(
                report_id=report.id,
                report_type=report.report_type,
                scope_type=report.scope_type,
                scope_id=report.scope_id,
                title=report.title,
                requested_by=report.requested_by,
                freshness_policy_hours=self.settings.external_risk_cache_ttl_hours,
            )
        )
        persisted = self.report_repository.get_report(report.id)
        if persisted is None:
            raise RuntimeError(f"Report {report.id} was not found after generation.")
        return ReportGenerationResult(report=persisted, output=output)

    def get_report(self, report_id: str) -> ReportRecord | None:
        return self.report_repository.get_report(report_id)

    def list_reports(self, *, scope_type: str | None = None, status: ReportStatus | None = None, limit: int = 20):
        return self.report_repository.list_reports(
            scope_type=scope_type,
            status=status,
            limit=limit,
        )

    def _default_title(self, request: ReportRequest) -> str:
        if request.scope_type == ReportScopeType.DASHBOARD:
            return "Dashboard risk summary"
        if request.scope_type == ReportScopeType.PRODUCT:
            if request.scope_id is None:
                return "Product risk report"
            product = self.catalog_repository.get_product_by_id(int(request.scope_id))
            return f"Product risk report for {product.name}" if product is not None else "Product risk report"
        if request.scope_type == ReportScopeType.COUNTRY:
            return f"Country risk report for {(request.scope_id or '').upper()}".strip()
        if request.scope_type == ReportScopeType.SUPPLIER:
            if request.scope_id is None:
                return "Supplier risk report"
            supplier = self.catalog_repository.get_supplier_by_id(int(request.scope_id))
            return f"Supplier risk report for {supplier.name}" if supplier is not None else "Supplier risk report"
        return "Chat export report"
