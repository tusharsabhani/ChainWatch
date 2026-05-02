from __future__ import annotations

from app.adapters.llm import OpenAILLMAdapter
from app.evals.chat_routing import run_chat_routing_eval_suite
from app.adapters.search import SearchAdapter
from app.schemas.chat import ChatContextScope
from app.services.chat import ChatService


class FakeSearchAdapter(SearchAdapter):
    def __init__(self, results_by_country: dict[str, list[dict[str, object]]]) -> None:
        self.results_by_country = results_by_country

    def is_configured(self) -> bool:
        return True

    def search(self, query: str, **kwargs):
        country_code = str(kwargs.get("country_code", "")).upper()
        return list(self.results_by_country.get(country_code, []))


def _fake_search_adapter() -> FakeSearchAdapter:
    return FakeSearchAdapter(
        {
            "IN": [
                {
                    "title": "India customs backlog slows inbound processing",
                    "url": "https://example.com/india-customs",
                    "source_name": "Trade Desk",
                    "snippet": "Customs bottlenecks and queue growth are delaying inbound releases.",
                    "risk_type": "logistics",
                    "severity": 4,
                    "event_date": "2026-05-01",
                }
            ]
        }
    )


def test_chat_routing_eval_suite_passes_for_mock_openai_adapter() -> None:
    summary = run_chat_routing_eval_suite(OpenAILLMAdapter(api_key=None, model="gpt-5.2"))

    assert summary.failed_cases == 0
    assert summary.passed_cases == summary.total_cases


def test_chat_service_uses_mock_openai_semantic_routing_without_api_key(seeded_runtime) -> None:
    service = ChatService(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
        llm_adapter=OpenAILLMAdapter(api_key=None, model="gpt-5.2"),
        search_adapter=_fake_search_adapter(),
    )
    session = service.create_session(context_scope=ChatContextScope.GLOBAL)

    result = service.send_message(
        session_id=session.id,
        message="What customs bottlenecks and service-level issues should I watch this week?",
    )

    assert "External Risk Agent" in result.assistant_message.used_agents
    assert "Fulfillment Agent" in result.assistant_message.used_agents
    assert result.assistant_message.message_text
