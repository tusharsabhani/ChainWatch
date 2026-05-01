from __future__ import annotations

from app.schemas.common import CamelModel, FreshnessInfo


class ReportListItem(CamelModel):
    id: str
    title: str
    scope_type: str
    status: str
    created_at: str
    markdown_path: str | None = None


class ReportsListResponse(CamelModel):
    items: list[ReportListItem]


class ReportDetailResponse(CamelModel):
    id: str
    title: str
    scope_type: str
    scope_id: str | None = None
    status: str
    summary: str | None = None
    json_path: str | None = None
    markdown_path: str | None = None
    markdown_preview: str | None = None
    created_at: str
    completed_at: str | None = None
    freshness: FreshnessInfo | None = None


class ReportGenerateRequest(CamelModel):
    scope_type: str
    scope_id: str | None = None
    report_type: str
    title: str | None = None


class ReportGenerateResponse(CamelModel):
    id: str
    status: str
    scope_type: str
    scope_id: str | None = None
    created_at: str
