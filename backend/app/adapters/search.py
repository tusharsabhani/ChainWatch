from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


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

