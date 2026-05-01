from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMAdapter(ABC):
    @abstractmethod
    def is_configured(self) -> bool:
        """Return whether the adapter is configured for live use."""

    @abstractmethod
    def generate_completion(self, prompt: str, **kwargs: Any) -> str:
        """Generate a completion for a given prompt."""


class NullLLMAdapter(LLMAdapter):
    def is_configured(self) -> bool:
        return False

    def generate_completion(self, prompt: str, **kwargs: Any) -> str:
        raise RuntimeError("LLM provider is not configured.")

