from __future__ import annotations

from abc import ABC, abstractmethod
import json
import re
from typing import Any

from app.config import Settings
from app.schemas.llm import ChatToolDefinition, ChatToolName, ChatToolPlan, ChatToolSelection


class LLMAdapter(ABC):
    @abstractmethod
    def is_configured(self) -> bool:
        """Return whether the adapter is configured for live use."""

    @abstractmethod
    def generate_completion(self, prompt: str, **kwargs: Any) -> str:
        """Generate a completion for a given prompt."""

    def supports_routing(self) -> bool:
        return self.is_configured()

    def supports_composition(self) -> bool:
        return self.is_configured()

    def route_chat(
        self,
        *,
        user_message: str,
        context_scope: str,
        context_id: str | None,
        recent_history: list[dict[str, Any]],
        available_tools: list[ChatToolDefinition],
    ) -> ChatToolPlan:
        raise RuntimeError("Semantic routing is not available for the configured LLM adapter.")

    def compose_chat_answer(
        self,
        *,
        user_message: str,
        context_scope: str,
        context_id: str | None,
        recent_history: list[dict[str, Any]],
        agent_outputs: dict[str, dict[str, Any]],
        limitations: list[str],
        citations: list[dict[str, Any]],
    ) -> str:
        raise RuntimeError("Chat composition is not available for the configured LLM adapter.")


class NullLLMAdapter(LLMAdapter):
    def is_configured(self) -> bool:
        return False

    def generate_completion(self, prompt: str, **kwargs: Any) -> str:
        raise RuntimeError("LLM provider is not configured.")


class OpenAILLMAdapter(LLMAdapter):
    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key.strip() if api_key else None
        self.model = model
        self.base_url = base_url.strip() if base_url else None

    @property
    def mode(self) -> str:
        return "live" if self.is_configured() else "mock"

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def supports_routing(self) -> bool:
        return True

    def supports_composition(self) -> bool:
        return True

    def generate_completion(self, prompt: str, **kwargs: Any) -> str:
        if not self.is_configured():
            return self._mock_generate_completion(prompt)

        response = self._client().responses.create(
            model=self.model,
            instructions=(
                "You are the ChainWatch backend composer. Use only the supplied facts. "
                "Never invent data, sources, or citations."
            ),
            input=prompt,
            max_output_tokens=kwargs.get("max_output_tokens", 300),
        )
        if not response.output_text:
            raise RuntimeError("OpenAI returned an empty completion.")
        return response.output_text.strip()

    def route_chat(
        self,
        *,
        user_message: str,
        context_scope: str,
        context_id: str | None,
        recent_history: list[dict[str, Any]],
        available_tools: list[ChatToolDefinition],
    ) -> ChatToolPlan:
        if not self.is_configured():
            return self._mock_route_chat(
                user_message=user_message,
                context_scope=context_scope,
                context_id=context_id,
                available_tools=available_tools,
            )

        payload = {
            "userMessage": user_message,
            "contextScope": context_scope,
            "contextId": context_id,
            "recentHistory": recent_history[-6:],
            "availableTools": [tool.model_dump(mode="json") for tool in available_tools],
        }
        response = self._client().responses.create(
            model=self.model,
            instructions=(
                "You route ChainWatch chat requests to the smallest useful set of internal tools. "
                "Select only from the supplied tools. Prefer precision over coverage, but include multiple "
                "tools when the question clearly spans multiple operational domains."
            ),
            input=json.dumps(payload, sort_keys=True),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "chainwatch_chat_tool_plan",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "selected_tools": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "tool_name": {
                                            "type": "string",
                                            "enum": [tool.value for tool in ChatToolName],
                                        },
                                        "reason": {
                                            "type": "string",
                                        },
                                    },
                                    "required": ["tool_name", "reason"],
                                },
                            },
                            "routing_notes": {
                                "type": "string",
                            },
                        },
                        "required": ["selected_tools", "routing_notes"],
                    },
                }
            },
            max_output_tokens=220,
        )
        if not response.output_text:
            raise RuntimeError("OpenAI returned an empty routing plan.")
        return ChatToolPlan.model_validate(json.loads(response.output_text))

    def compose_chat_answer(
        self,
        *,
        user_message: str,
        context_scope: str,
        context_id: str | None,
        recent_history: list[dict[str, Any]],
        agent_outputs: dict[str, dict[str, Any]],
        limitations: list[str],
        citations: list[dict[str, Any]],
    ) -> str:
        if not self.is_configured():
            return self._mock_compose_chat_answer(
                user_message=user_message,
                agent_outputs=agent_outputs,
                limitations=limitations,
                citations=citations,
            )

        payload = {
            "userMessage": user_message,
            "contextScope": context_scope,
            "contextId": context_id,
            "recentHistory": recent_history[-6:],
            "agentOutputs": agent_outputs,
            "limitations": limitations,
            "citations": citations,
        }
        response = self._client().responses.create(
            model=self.model,
            instructions=(
                "You are the ChainWatch response composer. Answer using only the provided structured findings. "
                "Be concise, operational, and specific. Do not invent facts or imply external validation when "
                "citations are absent. If limitations are present, acknowledge them briefly at the end."
            ),
            input=json.dumps(payload, sort_keys=True),
            max_output_tokens=320,
        )
        if not response.output_text:
            raise RuntimeError("OpenAI returned an empty chat answer.")
        return response.output_text.strip()

    def _client(self):
        if not self.is_configured():
            raise RuntimeError("OpenAI live mode requires an API key.")
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - depends on local env sync state
            raise RuntimeError("OpenAI SDK is not installed. Run backend dependency sync again.") from exc

        client_kwargs: dict[str, Any] = {
            "api_key": self.api_key,
        }
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        return OpenAI(**client_kwargs)

    def _mock_generate_completion(self, prompt: str) -> str:
        condensed = " ".join(prompt.split())
        return f"[mock-openai] {condensed[:280]}".strip()

    def _mock_route_chat(
        self,
        *,
        user_message: str,
        context_scope: str,
        context_id: str | None,
        available_tools: list[ChatToolDefinition],
    ) -> ChatToolPlan:
        normalized = _normalize_text(user_message)
        tool_scores: dict[ChatToolName, int] = {}
        tool_matches: dict[ChatToolName, list[str]] = {}

        for tool in available_tools:
            score = 0
            matches: list[str] = []
            for cue in tool.cues:
                if _contains_phrase(normalized, cue):
                    score += 3
                    matches.append(cue)
            for token in _tokenize(tool.purpose):
                if len(token) < 4:
                    continue
                if token in normalized:
                    score += 1
                    matches.append(token)

            if context_scope in {"country", "supplier"} and tool.name == ChatToolName.EXTERNAL_RISK:
                score += 2
                matches.append(f"{context_scope}_scope")
            if context_scope == "product" and tool.name in {
                ChatToolName.DEMAND,
                ChatToolName.INVENTORY,
                ChatToolName.FULFILLMENT,
            }:
                score += 1
                matches.append("product_scope")
            if score > 0:
                tool_scores[tool.name] = score
                tool_matches[tool.name] = matches

        ranked_tools = sorted(
            tool_scores.items(),
            key=lambda item: (-item[1], item[0].value),
        )
        selected = [
            ChatToolSelection(
                tool_name=tool_name,
                reason=f"Matched cues: {', '.join(list(dict.fromkeys(tool_matches[tool_name]))[:3])}",
            )
            for tool_name, score in ranked_tools
            if score >= 2
        ]

        if context_scope == "product" and selected:
            overview_cues = {
                "risk summary",
                "risk overview",
                "overall risk",
                "operational risk",
            }
            if any(_contains_phrase(normalized, cue) for cue in overview_cues):
                selected_names = {item.tool_name for item in selected}
                if ChatToolName.EXTERNAL_RISK not in selected_names:
                    selected.append(
                        ChatToolSelection(
                            tool_name=ChatToolName.EXTERNAL_RISK,
                            reason="Added external risk because the product question asked for an overall risk view.",
                        )
                    )

        if not selected:
            if context_scope in {"country", "supplier"}:
                selected = [
                    ChatToolSelection(
                        tool_name=ChatToolName.EXTERNAL_RISK,
                        reason=f"Defaulted to external risk because the scope is {context_scope}.",
                    )
                ]
            elif context_scope == "product" and context_id:
                selected = [
                    ChatToolSelection(
                        tool_name=ChatToolName.DEMAND,
                        reason="Defaulted to product demand analysis for a product-scoped question.",
                    ),
                    ChatToolSelection(
                        tool_name=ChatToolName.INVENTORY,
                        reason="Defaulted to inventory analysis for a product-scoped question.",
                    ),
                    ChatToolSelection(
                        tool_name=ChatToolName.FULFILLMENT,
                        reason="Defaulted to fulfillment analysis for a product-scoped question.",
                    ),
                    ChatToolSelection(
                        tool_name=ChatToolName.EXTERNAL_RISK,
                        reason="Included external risk to capture supplier-country exposure for the product.",
                    ),
                ]
            else:
                selected = [
                    ChatToolSelection(
                        tool_name=ChatToolName.EXTERNAL_RISK,
                        reason="Defaulted to a broad risk overview for an unclassified global question.",
                    ),
                    ChatToolSelection(
                        tool_name=ChatToolName.INVENTORY,
                        reason="Included inventory because stock health is a core operational default view.",
                    ),
                    ChatToolSelection(
                        tool_name=ChatToolName.FULFILLMENT,
                        reason="Included fulfillment because delivery health is a core operational default view.",
                    ),
                ]

        return ChatToolPlan(
            selected_tools=selected,
            routing_notes="Mock OpenAI routing used local semantic cues because no API key was configured.",
        )

    def _mock_compose_chat_answer(
        self,
        *,
        user_message: str,
        agent_outputs: dict[str, dict[str, Any]],
        limitations: list[str],
        citations: list[dict[str, Any]],
    ) -> str:
        parts: list[str] = []

        external_output = agent_outputs.get("external_risk")
        if external_output is not None:
            parts.append(
                f"External risk is the clearest signal right now: {external_output.get('summary', '').strip()} "
                f"I found {len(external_output.get('risk_events', []))} active event(s) with maximum severity "
                f"{external_output.get('highest_severity', 'unknown')}."
            )

        demand_output = agent_outputs.get("demand")
        if demand_output is not None:
            parts.append(
                f"Demand outlook points to {demand_output.get('forecasted_units', 'unknown')} forecasted units "
                f"over {demand_output.get('forecast_window_days', 'unknown')} days with demand risk "
                f"{demand_output.get('demand_risk_score', 'unknown')}."
            )

        inventory_output = agent_outputs.get("inventory")
        if inventory_output is not None:
            cover_text = inventory_output.get("days_of_cover")
            if cover_text is None:
                cover_phrase = "with an unknown cover window"
            else:
                cover_phrase = f"with {cover_text} days of cover"
            parts.append(
                f"Inventory is currently {inventory_output.get('inventory_status', 'unknown')} {cover_phrase}; "
                f"recommended action: {inventory_output.get('recommended_action', 'review the latest stock position')}."
            )

        fulfillment_output = agent_outputs.get("fulfillment")
        if fulfillment_output is not None:
            on_time_rate = fulfillment_output.get("on_time_rate")
            on_time_text = "unknown"
            if isinstance(on_time_rate, (int, float)):
                on_time_text = f"{round(on_time_rate * 100, 1)}%"
            parts.append(
                f"Fulfillment health is at risk score {fulfillment_output.get('fulfillment_risk_score', 'unknown')}, "
                f"with backlog at {fulfillment_output.get('backlog_orders', 'unknown')} orders and on-time rate "
                f"{on_time_text}."
            )

        if not parts:
            parts.append(
                f"I could not find enough structured data to answer '{user_message}' yet, so the response is limited."
            )

        if citations:
            parts.append(f"I preserved {len(citations)} supporting citation(s) from the external risk workflow.")

        if limitations:
            parts.append("Limitations: " + "; ".join(dict.fromkeys(limitations)))

        return " ".join(part.strip() for part in parts if part).strip()


def build_llm_adapter(settings: Settings) -> LLMAdapter:
    provider = settings.resolved_llm_provider

    if not provider:
        return NullLLMAdapter()
    if provider == "openai":
        return OpenAILLMAdapter(
            api_key=settings.resolved_llm_api_key,
            model=settings.openai_model,
            base_url=settings.openai_base_url,
        )
    raise ValueError(f"Unsupported LLM provider: {provider}")


def _normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9\s]+", " ", value.lower())


def _contains_phrase(normalized_text: str, phrase: str) -> bool:
    return _normalize_text(phrase) in normalized_text


def _tokenize(value: str) -> list[str]:
    return [token for token in _normalize_text(value).split() if token]
