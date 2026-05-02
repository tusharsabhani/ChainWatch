from __future__ import annotations

from datetime import datetime, timezone
import json
import uuid

from app.adapters.llm import LLMAdapter, NullLLMAdapter
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
from app.schemas.agents import AgentRunStatus, AgentTriggerType, DemandSignal
from app.schemas.chat import (
    ChatConversation,
    ChatAgentTraceSummary,
    ChatContextScope,
    ChatHistoryMessage,
    ChatMessageRole,
    ChatOrchestratorInput,
    ChatOrchestratorOutput,
    ChatScope,
)
from app.schemas.llm import ChatToolDefinition, default_chat_tools
from app.services.citations import dedupe_citations
from app.services.storage import StorageManager

EXTERNAL_KEYWORDS = {
    "country",
    "countries",
    "supplier",
    "suppliers",
    "tariff",
    "tariffs",
    "shipping",
    "shipment",
    "disruption",
    "port",
    "weather",
    "strike",
    "trade",
    "risk",
}
DEMAND_KEYWORDS = {
    "demand",
    "seasonality",
    "seasonal",
    "forecast",
    "spike",
    "sales",
    "velocity",
}
INVENTORY_KEYWORDS = {
    "inventory",
    "stock",
    "stockout",
    "reorder",
    "cover",
    "on hand",
    "warehouse",
}
FULFILLMENT_KEYWORDS = {
    "fulfillment",
    "sla",
    "delay",
    "delays",
    "delivery",
    "backlog",
    "carrier",
    "late",
}


class ChatOrchestrator(BaseAgent):
    def __init__(
        self,
        *,
        settings: Settings,
        storage: StorageManager,
        database: SQLiteConnectionFactory,
        llm_adapter: LLMAdapter | None = None,
        search_adapter: SearchAdapter | None = None,
    ) -> None:
        super().__init__(
            agent_name="Chat Orchestrator",
            settings=settings,
            storage=storage,
            database=database,
        )
        self.catalog_repository = CatalogRepository(database)
        self.llm_adapter = llm_adapter or NullLLMAdapter()
        self.demand_agent = DemandAgent(
            settings=settings,
            storage=storage,
            database=database,
        )
        self.inventory_agent = InventoryAgent(
            settings=settings,
            storage=storage,
            database=database,
        )
        self.fulfillment_agent = FulfillmentAgent(
            settings=settings,
            storage=storage,
            database=database,
        )
        self.external_risk_agent = ExternalRiskAgent(
            settings=settings,
            storage=storage,
            database=database,
            search_adapter=search_adapter or NullSearchAdapter(),
        )

    def run(self, input_model: ChatOrchestratorInput) -> ChatOrchestratorOutput:
        trace = self._start_trace(
            trigger_type=AgentTriggerType.CHAT,
            trigger_ref=input_model.session_id,
            input_payload=input_model,
        )

        used_agents: list[str] = []
        limitations: list[str] = []
        citations = []
        trace_summary: list[ChatAgentTraceSummary] = []
        agent_outputs: dict[str, object] = {}

        try:
            selection, routing_limitations = self._select_agents(input_model)
            limitations.extend(routing_limitations)
            scope_inputs = self._resolve_scope_inputs(input_model)

            if "external_risk" in selection:
                try:
                    external_output = self.external_risk_agent.run(
                        self._build_external_input(
                            input_model=input_model,
                            country_codes=scope_inputs["country_codes"],
                        )
                    )
                    used_agents.append("External Risk Agent")
                    citations.extend(external_output.citations)
                    limitations.extend(external_output.limitations)
                    trace_summary.append(
                        ChatAgentTraceSummary(
                            agent_name="External Risk Agent",
                            status=self._external_status(external_output),
                            summary=external_output.summary,
                            limitations=list(external_output.limitations),
                            data_source=external_output.data_source,
                        )
                    )
                    agent_outputs["external_risk"] = external_output
                except Exception as exc:
                    limitations.append(f"External Risk Agent failed: {exc}")
                    trace_summary.append(
                        ChatAgentTraceSummary(
                            agent_name="External Risk Agent",
                            status=AgentRunStatus.FAILED,
                            summary="External risk analysis failed.",
                            limitations=[str(exc)],
                        )
                    )

            if "demand" in selection and scope_inputs["product_ids"]:
                try:
                    demand_output = self.demand_agent.run(
                        self._build_demand_input(
                            input_model=input_model,
                            product_ids=scope_inputs["product_ids"],
                        )
                    )
                    used_agents.append("Demand Agent")
                    if demand_output.low_confidence:
                        limitations.extend(demand_output.supporting_notes)
                    trace_summary.append(
                        ChatAgentTraceSummary(
                            agent_name="Demand Agent",
                            status=AgentRunStatus.PARTIAL if demand_output.low_confidence else AgentRunStatus.COMPLETED,
                            summary=(
                                f"Forecasted {demand_output.forecasted_units} units over "
                                f"{demand_output.forecast_window_days} days."
                            ),
                            limitations=demand_output.supporting_notes if demand_output.low_confidence else [],
                        )
                    )
                    agent_outputs["demand"] = demand_output
                except Exception as exc:
                    limitations.append(f"Demand Agent failed: {exc}")
                    trace_summary.append(
                        ChatAgentTraceSummary(
                            agent_name="Demand Agent",
                            status=AgentRunStatus.FAILED,
                            summary="Demand analysis failed.",
                            limitations=[str(exc)],
                        )
                    )

            if "inventory" in selection and scope_inputs["product_ids"]:
                try:
                    demand_signals = self._demand_signals_for_scope(
                        product_ids=scope_inputs["product_ids"],
                        demand_output=agent_outputs.get("demand"),
                    )
                    inventory_output = self.inventory_agent.run(
                        self._build_inventory_input(
                            input_model=input_model,
                            product_ids=scope_inputs["product_ids"],
                            demand_signals=demand_signals,
                        )
                    )
                    used_agents.append("Inventory Agent")
                    if inventory_output.partial:
                        limitations.extend(inventory_output.supporting_notes)
                    trace_summary.append(
                        ChatAgentTraceSummary(
                            agent_name="Inventory Agent",
                            status=AgentRunStatus.PARTIAL if inventory_output.partial else AgentRunStatus.COMPLETED,
                            summary=(
                                f"Inventory is {inventory_output.inventory_status} with "
                                f"{inventory_output.stockout_risk_score} stockout risk."
                            ),
                            limitations=list(inventory_output.supporting_notes),
                        )
                    )
                    agent_outputs["inventory"] = inventory_output
                except Exception as exc:
                    limitations.append(f"Inventory Agent failed: {exc}")
                    trace_summary.append(
                        ChatAgentTraceSummary(
                            agent_name="Inventory Agent",
                            status=AgentRunStatus.FAILED,
                            summary="Inventory analysis failed.",
                            limitations=[str(exc)],
                        )
                    )

            if "fulfillment" in selection and (scope_inputs["product_ids"] or input_model.context_scope == ChatContextScope.GLOBAL):
                try:
                    fulfillment_output = self.fulfillment_agent.run(
                        self._build_fulfillment_input(
                            input_model=input_model,
                            product_ids=scope_inputs["product_ids"],
                            external_risk_events=getattr(agent_outputs.get("external_risk"), "risk_events", []),
                        )
                    )
                    used_agents.append("Fulfillment Agent")
                    if fulfillment_output.partial:
                        limitations.extend(fulfillment_output.supporting_notes)
                    trace_summary.append(
                        ChatAgentTraceSummary(
                            agent_name="Fulfillment Agent",
                            status=AgentRunStatus.PARTIAL if fulfillment_output.partial else AgentRunStatus.COMPLETED,
                            summary=(
                                f"Fulfillment risk is {fulfillment_output.fulfillment_risk_score} with "
                                f"{round(fulfillment_output.on_time_rate * 100, 1)}% on-time rate."
                            ),
                            limitations=list(fulfillment_output.supporting_notes),
                        )
                    )
                    agent_outputs["fulfillment"] = fulfillment_output
                except Exception as exc:
                    limitations.append(f"Fulfillment Agent failed: {exc}")
                    trace_summary.append(
                        ChatAgentTraceSummary(
                            agent_name="Fulfillment Agent",
                            status=AgentRunStatus.FAILED,
                            summary="Fulfillment analysis failed.",
                            limitations=[str(exc)],
                        )
                    )

            assistant_message = self._compose_message(
                input_model=input_model,
                agent_outputs=agent_outputs,
                citations=citations,
                limitations=limitations,
            )
            output = ChatOrchestratorOutput(
                assistant_message=assistant_message,
                used_agents=used_agents,
                citations=dedupe_citations(citations),
                scope=ChatScope(
                    context_scope=input_model.context_scope,
                    context_id=input_model.context_id,
                ),
                limitations=list(dict.fromkeys(limitations)),
                agent_trace_summary=trace_summary,
            )
            self._finish_trace(
                trace,
                status=self._trace_status(
                    partial=bool(output.limitations),
                    failed=not output.used_agents and not agent_outputs,
                ),
                output_payload=output,
                error_message="; ".join(output.limitations[:3]) if output.limitations else None,
            )
            return output
        except Exception as exc:
            output = ChatOrchestratorOutput(
                assistant_message="I could not finish processing this question.",
                used_agents=used_agents,
                citations=dedupe_citations(citations),
                scope=ChatScope(
                    context_scope=input_model.context_scope,
                    context_id=input_model.context_id,
                ),
                limitations=list(dict.fromkeys([*limitations, str(exc)])),
                agent_trace_summary=trace_summary,
            )
            self._finish_trace(
                trace,
                status=AgentRunStatus.FAILED,
                output_payload=output,
                error_message=str(exc),
            )
            return output

    def _select_agents(self, input_model: ChatOrchestratorInput) -> tuple[list[str], list[str]]:
        routing_limitations: list[str] = []
        available_tools = self._available_tools()

        if self.llm_adapter.supports_routing():
            try:
                plan = self.llm_adapter.route_chat(
                    user_message=input_model.user_message,
                    context_scope=input_model.context_scope.value,
                    context_id=input_model.context_id,
                    recent_history=[item.model_dump(mode="json") for item in input_model.recent_history[-6:]],
                    available_tools=available_tools,
                )
                selected = [item.tool_name.value for item in plan.selected_tools]
                if selected:
                    return list(dict.fromkeys(selected)), routing_limitations
                routing_limitations.append("LLM routing returned no tool plan, so heuristic routing was used.")
            except Exception as exc:
                routing_limitations.append(f"LLM routing failed: {exc}")

        return self._heuristic_agent_selection(input_model), routing_limitations

    def _heuristic_agent_selection(self, input_model: ChatOrchestratorInput) -> list[str]:
        message = input_model.user_message.lower()
        selected: list[str] = []

        if any(keyword in message for keyword in EXTERNAL_KEYWORDS):
            selected.append("external_risk")
        if any(keyword in message for keyword in DEMAND_KEYWORDS):
            selected.append("demand")
        if any(keyword in message for keyword in INVENTORY_KEYWORDS):
            selected.append("inventory")
        if any(keyword in message for keyword in FULFILLMENT_KEYWORDS):
            selected.append("fulfillment")

        if selected:
            return selected

        if input_model.context_scope in {ChatContextScope.COUNTRY, ChatContextScope.SUPPLIER}:
            return ["external_risk"]
        if input_model.context_scope == ChatContextScope.PRODUCT:
            return ["demand", "inventory", "fulfillment", "external_risk"]
        return ["demand", "inventory", "fulfillment", "external_risk"]

    def _available_tools(self) -> list[ChatToolDefinition]:
        return default_chat_tools()

    def _resolve_scope_inputs(self, input_model: ChatOrchestratorInput) -> dict[str, list[str] | list[int]]:
        if input_model.context_scope == ChatContextScope.GLOBAL:
            return {
                "product_ids": self.catalog_repository.list_all_product_ids(),
                "country_codes": self.catalog_repository.list_all_supplier_country_codes(),
            }

        if input_model.context_scope == ChatContextScope.PRODUCT:
            if input_model.context_id is None:
                return {"product_ids": [], "country_codes": []}
            product = self.catalog_repository.get_product_by_id(int(input_model.context_id))
            if product is None:
                return {"product_ids": [], "country_codes": []}
            return {
                "product_ids": [product.id],
                "country_codes": self.catalog_repository.list_supplier_country_codes_for_product_ids([product.id]),
            }

        if input_model.context_scope == ChatContextScope.SUPPLIER:
            if input_model.context_id is None:
                return {"product_ids": [], "country_codes": []}
            supplier = self.catalog_repository.get_supplier_by_id(int(input_model.context_id))
            return {
                "product_ids": [],
                "country_codes": [supplier.country_code] if supplier is not None else [],
            }

        if input_model.context_scope == ChatContextScope.COUNTRY:
            return {
                "product_ids": [],
                "country_codes": [str(input_model.context_id or "").upper()] if input_model.context_id else [],
            }

        return {"product_ids": [], "country_codes": []}

    def _build_demand_input(self, *, input_model: ChatOrchestratorInput, product_ids: list[int]):
        from app.schemas.agents import DemandAgentInput

        return DemandAgentInput(
            product_ids=product_ids,
            trigger_type=AgentTriggerType.CHAT,
            trigger_ref=input_model.session_id,
        )

    def _build_inventory_input(self, *, input_model: ChatOrchestratorInput, product_ids: list[int], demand_signals: list[DemandSignal]):
        from app.schemas.agents import InventoryAgentInput

        return InventoryAgentInput(
            product_ids=product_ids,
            demand_signals=demand_signals,
            trigger_type=AgentTriggerType.CHAT,
            trigger_ref=input_model.session_id,
        )

    def _build_fulfillment_input(self, *, input_model: ChatOrchestratorInput, product_ids: list[int], external_risk_events: list[object]):
        from app.schemas.agents import FulfillmentAgentInput

        return FulfillmentAgentInput(
            product_ids=product_ids,
            external_risk_events=external_risk_events,
            trigger_type=AgentTriggerType.CHAT,
            trigger_ref=input_model.session_id,
        )

    def _build_external_input(self, *, input_model: ChatOrchestratorInput, country_codes: list[str]):
        from app.schemas.agents import ExternalRiskAgentInput

        return ExternalRiskAgentInput(
            country_codes=country_codes,
            freshness_policy_hours=self.settings.external_risk_cache_ttl_hours,
            trigger_type=AgentTriggerType.CHAT,
            trigger_ref=input_model.session_id,
        )

    def _demand_signals_for_scope(self, *, product_ids: list[int], demand_output: object | None) -> list[DemandSignal]:
        if demand_output is None or len(product_ids) != 1:
            return []
        return [
            DemandSignal(
                product_id=product_ids[0],
                forecast_window_days=demand_output.forecast_window_days,
                forecasted_units=demand_output.forecasted_units,
                demand_risk_score=demand_output.demand_risk_score,
            )
        ]

    def _external_status(self, external_output) -> AgentRunStatus:
        if external_output.data_source == "fresh" and not external_output.limitations:
            return AgentRunStatus.COMPLETED
        if external_output.data_source == "empty" and external_output.limitations:
            return AgentRunStatus.FAILED
        return AgentRunStatus.PARTIAL

    def _compose_message(
        self,
        *,
        input_model: ChatOrchestratorInput,
        agent_outputs: dict[str, object],
        citations: list[object],
        limitations: list[str],
    ) -> str:
        if self.llm_adapter.supports_composition():
            try:
                return self.llm_adapter.compose_chat_answer(
                    user_message=input_model.user_message,
                    context_scope=input_model.context_scope.value,
                    context_id=input_model.context_id,
                    recent_history=[item.model_dump(mode="json") for item in input_model.recent_history[-6:]],
                    agent_outputs=self._serialize_agent_outputs(agent_outputs),
                    limitations=list(dict.fromkeys(limitations)),
                    citations=[item.model_dump(mode="json") for item in citations],
                )
            except Exception as exc:
                limitations.append(f"LLM composition failed: {exc}")

        return self._build_deterministic_message(agent_outputs=agent_outputs, limitations=limitations)

    def _build_llm_prompt(
        self,
        *,
        input_model: ChatOrchestratorInput,
        agent_outputs: dict[str, object],
        limitations: list[str],
    ) -> str:
        payload = {
            "sessionId": input_model.session_id,
            "contextScope": input_model.context_scope.value,
            "contextId": input_model.context_id,
            "userMessage": input_model.user_message,
            "recentHistory": [item.model_dump(mode="json") for item in input_model.recent_history[-6:]],
            "agentOutputs": {
                key: value.model_dump(mode="json")
                for key, value in agent_outputs.items()
            },
            "limitations": limitations,
        }
        return (
            "Write a concise ChainWatch answer using only the structured findings below. "
            "Do not invent facts or citations.\n\n"
            f"{json.dumps(payload, indent=2, sort_keys=True)}"
        )

    def _serialize_agent_outputs(self, agent_outputs: dict[str, object]) -> dict[str, dict[str, object]]:
        return {
            key: value.model_dump(mode="json")
            for key, value in agent_outputs.items()
        }

    def _build_deterministic_message(self, *, agent_outputs: dict[str, object], limitations: list[str]) -> str:
        parts: list[str] = []

        external_output = agent_outputs.get("external_risk")
        if external_output is not None:
            parts.append(
                f"External risk found {len(external_output.risk_events)} active event(s) with highest severity "
                f"{external_output.highest_severity}. {external_output.summary}"
            )

        demand_output = agent_outputs.get("demand")
        if demand_output is not None:
            parts.append(
                f"Demand forecast is {demand_output.forecasted_units} units over "
                f"{demand_output.forecast_window_days} days with risk score {demand_output.demand_risk_score}."
            )

        inventory_output = agent_outputs.get("inventory")
        if inventory_output is not None:
            cover_text = (
                f"{inventory_output.days_of_cover} days of cover"
                if inventory_output.days_of_cover is not None
                else "unknown days of cover"
            )
            parts.append(
                f"Inventory is {inventory_output.inventory_status} with {cover_text} and recommendation: "
                f"{inventory_output.recommended_action}"
            )

        fulfillment_output = agent_outputs.get("fulfillment")
        if fulfillment_output is not None:
            parts.append(
                f"Fulfillment risk is {fulfillment_output.fulfillment_risk_score}, backlog is "
                f"{fulfillment_output.backlog_orders}, and on-time rate is "
                f"{round(fulfillment_output.on_time_rate * 100, 1)}%."
            )

        if not parts:
            parts.append("I could not find enough structured data to answer this yet.")

        if limitations:
            parts.append("Limitations: " + "; ".join(dict.fromkeys(limitations)))

        return " ".join(parts).strip()


class ChatService:
    def __init__(
        self,
        *,
        settings: Settings,
        storage: StorageManager,
        database: SQLiteConnectionFactory,
        llm_adapter: LLMAdapter | None = None,
        search_adapter: SearchAdapter | None = None,
    ) -> None:
        self.chat_repository = ChatRepository(database)
        self.orchestrator = ChatOrchestrator(
            settings=settings,
            storage=storage,
            database=database,
            llm_adapter=llm_adapter,
            search_adapter=search_adapter,
        )

    def create_session(self, *, title: str | None = None, context_scope: ChatContextScope = ChatContextScope.GLOBAL, context_id: str | None = None):
        session_id = f"chat_{uuid.uuid4().hex[:12]}"
        resolved_title = title or self._default_title(context_scope=context_scope, context_id=context_id)
        return self.chat_repository.create_session(
            session_id=session_id,
            title=resolved_title,
            context_scope=context_scope,
            context_id=context_id,
        )

    def list_sessions(self, *, limit: int = 20):
        return self.chat_repository.list_sessions(limit=limit)

    def get_conversation(self, session_id: str):
        session = self.chat_repository.get_session(session_id)
        if session is None:
            raise ValueError(f"Chat session {session_id} was not found.")
        return ChatConversation(
            session=session,
            messages=self.chat_repository.list_messages(session_id),
        )

    def send_message(self, *, session_id: str, message: str):
        session = self.chat_repository.get_session(session_id)
        if session is None:
            raise ValueError(f"Chat session {session_id} was not found.")

        user_message = self.chat_repository.create_message(
            message_id=f"msg_{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            role=ChatMessageRole.USER,
            message_text=message,
        )
        self.chat_repository.touch_session(session_id=session_id, touched_at=user_message.created_at)

        if session.title == "New chat":
            trimmed = message.strip()[:60]
            self.chat_repository.update_session_title(
                session_id=session_id,
                title=trimmed or session.title,
            )

        history = [
            ChatHistoryMessage(role=item.role, message_text=item.message_text)
            for item in self.chat_repository.list_messages(session_id)
        ]
        output = self.orchestrator.run(
            ChatOrchestratorInput(
                session_id=session_id,
                user_message=message,
                context_scope=session.context_scope,
                context_id=session.context_id,
                recent_history=history[-8:],
            )
        )
        assistant_message = self.chat_repository.create_message(
            message_id=f"msg_{uuid.uuid4().hex[:12]}",
            session_id=session_id,
            role=ChatMessageRole.ASSISTANT,
            message_text=output.assistant_message,
            citations=output.citations,
            used_agents=output.used_agents,
            limitations=output.limitations,
            agent_trace_summary=output.agent_trace_summary,
        )
        self.chat_repository.touch_session(session_id=session_id, touched_at=assistant_message.created_at)
        from app.schemas.chat import ChatPostResult

        return ChatPostResult(
            user_message=user_message,
            assistant_message=assistant_message,
        )

    def _default_title(self, *, context_scope: ChatContextScope, context_id: str | None) -> str:
        if context_scope == ChatContextScope.GLOBAL:
            return "New chat"
        if context_id:
            return f"{context_scope.value.title()} chat: {context_id}"
        return f"{context_scope.value.title()} chat"
