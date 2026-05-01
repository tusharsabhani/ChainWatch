from __future__ import annotations

from app.schemas.agents import Citation


def normalize_citation(
    *,
    title: str | None,
    url: str | None,
    source_name: str | None,
    snippet: str | None = None,
) -> Citation | None:
    if not title or not url or not source_name:
        return None
    return Citation(
        title=title.strip(),
        url=url.strip(),
        source_name=source_name.strip(),
        snippet=snippet.strip() if snippet else None,
    )


def dedupe_citations(citations: list[Citation]) -> list[Citation]:
    seen_urls: set[str] = set()
    unique_citations: list[Citation] = []
    for citation in citations:
        if citation.url in seen_urls:
            continue
        seen_urls.add(citation.url)
        unique_citations.append(citation)
    return unique_citations
