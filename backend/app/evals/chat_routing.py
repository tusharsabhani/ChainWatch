from __future__ import annotations

from pydantic import BaseModel, Field

from app.adapters.llm import LLMAdapter
from app.schemas.chat import ChatContextScope
from app.schemas.llm import ChatToolName, default_chat_tools


class ChatRoutingEvalCase(BaseModel):
    case_id: str
    user_message: str
    context_scope: ChatContextScope = ChatContextScope.GLOBAL
    context_id: str | None = None
    expected_tools: list[ChatToolName] = Field(default_factory=list)
    forbidden_tools: list[ChatToolName] = Field(default_factory=list)


class ChatRoutingEvalResult(BaseModel):
    case_id: str
    passed: bool
    selected_tools: list[ChatToolName] = Field(default_factory=list)
    missing_tools: list[ChatToolName] = Field(default_factory=list)
    unexpected_tools: list[ChatToolName] = Field(default_factory=list)
    routing_notes: str


class ChatRoutingEvalSummary(BaseModel):
    total_cases: int
    passed_cases: int
    failed_cases: int
    results: list[ChatRoutingEvalResult] = Field(default_factory=list)


DEFAULT_CHAT_ROUTING_EVAL_CASES = [
    ChatRoutingEvalCase(
        case_id="external_customs_pressure",
        user_message="Which supplier countries are seeing customs bottlenecks or port congestion this week?",
        expected_tools=[ChatToolName.EXTERNAL_RISK],
        forbidden_tools=[ChatToolName.DEMAND, ChatToolName.INVENTORY],
    ),
    ChatRoutingEvalCase(
        case_id="product_stockout_pressure",
        user_message="Are we building stockout pressure on this SKU next month given current sell-through?",
        context_scope=ChatContextScope.PRODUCT,
        context_id="1",
        expected_tools=[ChatToolName.DEMAND, ChatToolName.INVENTORY],
    ),
    ChatRoutingEvalCase(
        case_id="service_level_pressure",
        user_message="Where are service-level misses and carrier delays creating the most delivery pressure?",
        expected_tools=[ChatToolName.FULFILLMENT],
    ),
    ChatRoutingEvalCase(
        case_id="product_full_risk_overview",
        user_message="Give me the biggest operational risk summary for this product.",
        context_scope=ChatContextScope.PRODUCT,
        context_id="2",
        expected_tools=[
            ChatToolName.DEMAND,
            ChatToolName.INVENTORY,
            ChatToolName.FULFILLMENT,
            ChatToolName.EXTERNAL_RISK,
        ],
    ),
]


def run_chat_routing_eval_suite(
    llm_adapter: LLMAdapter,
    *,
    cases: list[ChatRoutingEvalCase] | None = None,
) -> ChatRoutingEvalSummary:
    if not llm_adapter.supports_routing():
        raise RuntimeError("The configured LLM adapter does not support semantic routing evals.")

    resolved_cases = cases or DEFAULT_CHAT_ROUTING_EVAL_CASES
    results: list[ChatRoutingEvalResult] = []

    for case in resolved_cases:
        plan = llm_adapter.route_chat(
            user_message=case.user_message,
            context_scope=case.context_scope.value,
            context_id=case.context_id,
            recent_history=[],
            available_tools=default_chat_tools(),
        )
        selected_tools = [item.tool_name for item in plan.selected_tools]
        missing_tools = [tool for tool in case.expected_tools if tool not in selected_tools]
        unexpected_tools = [tool for tool in case.forbidden_tools if tool in selected_tools]

        results.append(
            ChatRoutingEvalResult(
                case_id=case.case_id,
                passed=not missing_tools and not unexpected_tools,
                selected_tools=selected_tools,
                missing_tools=missing_tools,
                unexpected_tools=unexpected_tools,
                routing_notes=plan.routing_notes,
            )
        )

    passed_cases = sum(1 for result in results if result.passed)
    return ChatRoutingEvalSummary(
        total_cases=len(results),
        passed_cases=passed_cases,
        failed_cases=len(results) - passed_cases,
        results=results,
    )
