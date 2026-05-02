from __future__ import annotations

from app.adapters.llm import NullLLMAdapter, OpenAILLMAdapter, build_llm_adapter
from app.config import Settings
from app.schemas.llm import ChatToolDefinition, ChatToolName, default_chat_tools


def test_build_llm_adapter_returns_null_when_llm_is_unconfigured(tmp_path) -> None:
    settings = Settings(repo_root=tmp_path, _env_file=None)

    adapter = build_llm_adapter(settings)

    assert isinstance(adapter, NullLLMAdapter)


def test_build_llm_adapter_returns_mock_openai_when_provider_has_no_key(tmp_path) -> None:
    settings = Settings(
        repo_root=tmp_path,
        _env_file=None,
        llm_provider="openai",
    )

    adapter = build_llm_adapter(settings)

    assert isinstance(adapter, OpenAILLMAdapter)
    assert adapter.mode == "mock"
    assert adapter.supports_routing() is True
    assert adapter.supports_composition() is True
    assert settings.llm_configured is False


def test_build_llm_adapter_returns_live_openai_when_api_key_is_present(tmp_path) -> None:
    settings = Settings(
        repo_root=tmp_path,
        _env_file=None,
        llm_provider="openai",
        openai_api_key="test-openai-key",
    )

    adapter = build_llm_adapter(settings)

    assert isinstance(adapter, OpenAILLMAdapter)
    assert adapter.mode == "live"
    assert adapter.is_configured() is True
    assert settings.llm_configured is True


def test_mock_openai_route_chat_selects_semantic_tools() -> None:
    adapter = OpenAILLMAdapter(api_key=None, model="gpt-5.2")
    available_tools = default_chat_tools()

    plan = adapter.route_chat(
        user_message="What customs bottlenecks and service-level misses should I watch this week?",
        context_scope="global",
        context_id=None,
        recent_history=[],
        available_tools=available_tools,
    )

    selected = [item.tool_name for item in plan.selected_tools]
    assert ChatToolName.EXTERNAL_RISK in selected
    assert ChatToolName.FULFILLMENT in selected
    assert "Mock OpenAI routing" in plan.routing_notes


def test_mock_openai_compose_uses_structured_agent_outputs_and_limitations() -> None:
    adapter = OpenAILLMAdapter(api_key=None, model="gpt-5.2")

    message = adapter.compose_chat_answer(
        user_message="What is most at risk?",
        context_scope="global",
        context_id=None,
        recent_history=[],
        agent_outputs={
            "external_risk": {
                "summary": "Port congestion in India is slowing inbound transfers.",
                "risk_events": [{"title": "India port congestion"}],
                "highest_severity": 4,
            },
            "inventory": {
                "inventory_status": "watch",
                "days_of_cover": 8.0,
                "recommended_action": "Reorder the next inbound batch sooner.",
            },
        },
        limitations=["Using cached external risk results."],
        citations=[{"title": "India port congestion"}],
    )

    assert "Port congestion in India" in message
    assert "8.0 days of cover" in message
    assert "Using cached external risk results." in message
    assert "citation" in message.lower()
