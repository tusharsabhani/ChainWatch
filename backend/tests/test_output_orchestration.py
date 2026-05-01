from __future__ import annotations

from app.adapters.search import SearchAdapter
from app.db.repositories.system_repository import SystemRepository
from app.schemas.chat import ChatContextScope
from app.schemas.reports import ReportRequest, ReportScopeType, ReportStatus, ReportType
from app.services.chat import ChatService
from app.services.reports import ReportService


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
                    "title": "Port congestion slows India imports",
                    "url": "https://example.com/india-port",
                    "source_name": "Trade Desk",
                    "snippet": "Congestion is increasing unloading delays and inland transfer pressure.",
                    "risk_type": "logistics",
                    "severity": 4,
                    "event_date": "2026-05-01",
                }
            ],
            "VN": [
                {
                    "title": "Vietnam labor action affects export throughput",
                    "url": "https://example.com/vietnam-labor",
                    "source_name": "Supply Pulse",
                    "snippet": "A labor action is slowing throughput and adding schedule risk for exporters.",
                    "risk_type": "labor",
                    "severity": 5,
                    "event_date": "2026-05-01",
                }
            ],
        }
    )


def test_report_service_generates_country_artifacts_and_persists_metadata(seeded_runtime) -> None:
    service = ReportService(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
        search_adapter=_fake_search_adapter(),
    )

    result = service.generate_report(
        ReportRequest(
            report_type=ReportType.COUNTRY_RISK,
            scope_type=ReportScopeType.COUNTRY,
            scope_id="IN",
        )
    )

    assert result.report.status == ReportStatus.COMPLETED
    assert result.report.json_path is not None
    assert result.report.markdown_path is not None
    assert result.output.report_markdown is not None
    assert result.output.summary

    json_path = seeded_runtime.settings.repo_root / result.report.json_path
    markdown_path = seeded_runtime.settings.repo_root / result.report.markdown_path
    assert json_path.exists()
    assert markdown_path.exists()

    system_repository = SystemRepository(seeded_runtime.database)
    assert system_repository.count_rows("reports") == 1
    assert system_repository.count_rows("agent_runs") >= 2


def test_report_service_preserves_json_when_markdown_rendering_fails(seeded_runtime) -> None:
    service = ReportService(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
        search_adapter=_fake_search_adapter(),
    )

    def _boom(*args, **kwargs):
        raise RuntimeError("markdown boom")

    service.agent._render_markdown = _boom  # type: ignore[method-assign]

    result = service.generate_report(
        ReportRequest(
            report_type=ReportType.COUNTRY_RISK,
            scope_type=ReportScopeType.COUNTRY,
            scope_id="VN",
        )
    )

    assert result.report.status == ReportStatus.PARTIAL
    assert result.report.json_path is not None
    assert result.report.markdown_path is None
    assert result.report.error_message is not None
    assert "markdown boom" in result.report.error_message

    json_path = seeded_runtime.settings.repo_root / result.report.json_path
    assert json_path.exists()


def test_chat_service_persists_messages_and_returns_structured_answer(seeded_runtime) -> None:
    service = ChatService(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
        search_adapter=_fake_search_adapter(),
    )

    session = service.create_session(context_scope=ChatContextScope.GLOBAL)
    result = service.send_message(
        session_id=session.id,
        message="Why are shipping delays and backlog risk rising this week?",
    )

    assert result.user_message.role.value == "user"
    assert result.assistant_message.role.value == "assistant"
    assert result.assistant_message.used_agents
    assert "External Risk Agent" in result.assistant_message.used_agents
    assert result.assistant_message.citations
    assert result.assistant_message.message_text

    conversation = service.get_conversation(session.id)
    assert len(conversation.messages) == 2
    assert conversation.messages[-1].used_agents == result.assistant_message.used_agents

    system_repository = SystemRepository(seeded_runtime.database)
    assert system_repository.count_rows("chat_sessions") == 1
    assert system_repository.count_rows("chat_messages") == 2


def test_chat_service_handles_single_agent_failure_without_losing_response(seeded_runtime) -> None:
    service = ChatService(
        settings=seeded_runtime.settings,
        storage=seeded_runtime.storage,
        database=seeded_runtime.database,
        search_adapter=_fake_search_adapter(),
    )
    session = service.create_session(context_scope=ChatContextScope.GLOBAL)

    def _fail(*args, **kwargs):
        raise RuntimeError("fulfillment exploded")

    service.orchestrator.fulfillment_agent.run = _fail  # type: ignore[method-assign]

    result = service.send_message(
        session_id=session.id,
        message="What shipping delays and backlog issues should I watch?",
    )

    assert result.assistant_message.message_text
    assert "External Risk Agent" in result.assistant_message.used_agents
    assert any("Fulfillment Agent failed" in item for item in result.assistant_message.limitations)
    assert result.assistant_message.citations
