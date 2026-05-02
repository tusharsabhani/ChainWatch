from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.config import Settings


class SearchAdapter(ABC):
    @abstractmethod
    def is_configured(self) -> bool:
        """Return whether the adapter is configured for live use."""

    @abstractmethod
    def search(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        """Perform a search query and return normalized results."""


class NullSearchAdapter(SearchAdapter):
    def is_configured(self) -> bool:
        return False

    def search(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        raise RuntimeError("Search provider is not configured.")


def build_search_adapter(settings: Settings) -> SearchAdapter:
    provider = settings.resolved_search_provider
    api_key = settings.resolved_search_api_key

    if not provider or not api_key:
        return NullSearchAdapter()
    if provider == "exa":
        from app.adapters.exa_search import ExaSearchAdapter

        return ExaSearchAdapter(api_key=api_key)
    raise ValueError(f"Unsupported search provider: {provider}")
