from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from app.adapters.search import SearchAdapter


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _isoformat_z(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _source_name_from_url(url: str | None) -> str | None:
    if not url:
        return None
    hostname = urlparse(url).netloc.strip().lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    return hostname or None


class ExaSearchAdapter(SearchAdapter):
    search_url = "https://api.exa.ai/search"

    def __init__(
        self,
        *,
        api_key: str,
        timeout_seconds: float = 20.0,
        num_results: int = 5,
    ) -> None:
        self.api_key = api_key.strip()
        self.timeout_seconds = timeout_seconds
        self.num_results = num_results

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, **kwargs: Any) -> list[dict[str, Any]]:
        if not self.api_key:
            raise RuntimeError("Exa search provider is not configured.")

        country_code = str(kwargs.get("country_code") or "").strip().upper() or None
        payload = self._build_payload(query)
        response_payload = self._post_json(payload)
        results = response_payload.get("results")
        if not isinstance(results, list):
            return []

        normalized_results: list[dict[str, Any]] = []
        for result in results:
            if not isinstance(result, dict):
                continue
            normalized_results.append(self._normalize_result(result, country_code=country_code))
        return normalized_results

    def _build_payload(self, query: str) -> dict[str, Any]:
        recent_cutoff = _utc_now() - timedelta(days=14)
        return {
            "query": query,
            "type": "auto",
            "category": "news",
            "numResults": self.num_results,
            "contents": {
                "highlights": {
                    "query": query,
                },
                # Let Exa reuse its own crawl cache for a day as well.
                "maxAgeHours": 24,
            },
            "startPublishedDate": _isoformat_z(recent_cutoff),
        }

    def _post_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            self.search_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                response_payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Exa search request failed with status {exc.code}: {detail[:200]}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(f"Exa search request failed: {exc.reason}") from exc

        if not isinstance(response_payload, dict):
            raise RuntimeError("Exa search returned an unexpected payload.")
        return response_payload

    def _normalize_result(
        self,
        result: dict[str, Any],
        *,
        country_code: str | None,
    ) -> dict[str, Any]:
        url = str(result.get("url") or "").strip()
        highlights = result.get("highlights")
        highlight_lines = (
            [str(item).strip() for item in highlights if str(item).strip()]
            if isinstance(highlights, list)
            else []
        )
        snippet = " ".join(highlight_lines[:2]) or None

        normalized: dict[str, Any] = {
            "title": str(result.get("title") or "").strip(),
            "url": url,
            "source_name": _source_name_from_url(url),
            "snippet": snippet,
            "published_at": result.get("publishedDate"),
        }
        if country_code is not None:
            normalized["country_code"] = country_code
        return normalized
