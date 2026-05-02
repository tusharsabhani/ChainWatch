from __future__ import annotations

from app.adapters.exa_search import ExaSearchAdapter
from app.adapters.search import NullSearchAdapter, build_search_adapter
from app.config import Settings


def test_build_search_adapter_returns_null_when_search_is_unconfigured(tmp_path) -> None:
    settings = Settings(repo_root=tmp_path, _env_file=None)

    adapter = build_search_adapter(settings)

    assert isinstance(adapter, NullSearchAdapter)


def test_build_search_adapter_returns_exa_when_provider_is_configured(tmp_path) -> None:
    settings = Settings(
        repo_root=tmp_path,
        _env_file=None,
        search_provider="exa",
        search_api_key="test-exa-key",
    )

    adapter = build_search_adapter(settings)

    assert isinstance(adapter, ExaSearchAdapter)
    assert adapter.is_configured() is True


def test_exa_api_key_enables_search_without_explicit_provider(tmp_path) -> None:
    settings = Settings(
        repo_root=tmp_path,
        _env_file=None,
        exa_api_key="test-exa-key",
    )

    assert settings.resolved_search_provider == "exa"
    assert settings.resolved_search_api_key == "test-exa-key"
    assert settings.search_configured is True
    assert isinstance(build_search_adapter(settings), ExaSearchAdapter)


def test_exa_search_adapter_normalizes_search_results(monkeypatch) -> None:
    adapter = ExaSearchAdapter(api_key="test-exa-key")
    captured_payload: dict[str, object] = {}

    def fake_post_json(payload):
        nonlocal captured_payload
        captured_payload = payload
        return {
            "results": [
                {
                    "title": "Port delays disrupt inbound shipments in India",
                    "url": "https://example.com/in-port-delay",
                    "publishedDate": "2026-05-01T00:00:00Z",
                    "highlights": [
                        "Major shipping delays are affecting port throughput.",
                        "Container pickup windows are getting tighter.",
                    ],
                }
            ]
        }

    monkeypatch.setattr(adapter, "_post_json", fake_post_json)

    results = adapter.search("recent disruptions in India", country_code="IN")

    assert captured_payload["category"] == "news"
    assert captured_payload["numResults"] == 5
    assert captured_payload["contents"] == {
        "highlights": {
            "query": "recent disruptions in India",
        },
        "maxAgeHours": 24,
    }
    assert results == [
        {
            "title": "Port delays disrupt inbound shipments in India",
            "url": "https://example.com/in-port-delay",
            "source_name": "example.com",
            "snippet": (
                "Major shipping delays are affecting port throughput. "
                "Container pickup windows are getting tighter."
            ),
            "published_at": "2026-05-01T00:00:00Z",
            "country_code": "IN",
        }
    ]
