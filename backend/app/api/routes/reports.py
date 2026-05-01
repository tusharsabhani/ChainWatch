from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Query, Request

from app.api.dependencies import get_report_service, get_runtime
from app.api.errors import error_response
from app.schemas.common import FreshnessInfo
from app.schemas.reports import ReportRequest, ReportScopeType, ReportStatus, ReportType
from app.schemas.reports_api import (
    ReportDetailResponse,
    ReportGenerateRequest,
    ReportGenerateResponse,
    ReportListItem,
    ReportsListResponse,
)

router = APIRouter(prefix="/reports")


@router.get("", response_model=ReportsListResponse)
def get_reports(
    request: Request,
    scope_type: str | None = Query(default=None, alias="scopeType"),
    status: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
) -> ReportsListResponse:
    try:
        status_filter = ReportStatus(status) if status is not None else None
    except ValueError:
        return error_response(400, "invalid_report_scope", f"Unsupported report status: {status}")

    try:
        service = get_report_service(request)
        reports = service.list_reports(
            scope_type=scope_type,
            status=status_filter,
            limit=limit,
        )
        return ReportsListResponse(
            items=[
                ReportListItem(
                    id=report.id,
                    title=report.title,
                    scope_type=report.scope_type.value,
                    status=report.status.value,
                    created_at=report.created_at,
                    markdown_path=report.markdown_path,
                )
                for report in reports
            ]
        )
    except Exception as exc:
        return error_response(500, "reports_unavailable", str(exc))


@router.get("/{report_id}", response_model=ReportDetailResponse)
def get_report_detail(request: Request, report_id: str) -> ReportDetailResponse:
    service = get_report_service(request)
    report = service.get_report(report_id)
    if report is None:
        return error_response(404, "report_not_found", f"Report {report_id} was not found.")

    runtime = get_runtime(request)
    markdown_preview: str | None = None
    if report.markdown_path:
        markdown_path = runtime.settings.repo_root / report.markdown_path
        if markdown_path.exists():
            markdown_preview = markdown_path.read_text(encoding="utf-8")[:4000]

    return ReportDetailResponse(
        id=report.id,
        title=report.title,
        scope_type=report.scope_type.value,
        scope_id=report.scope_id,
        status=report.status.value,
        summary=report.summary,
        json_path=report.json_path,
        markdown_path=report.markdown_path,
        markdown_preview=markdown_preview,
        created_at=report.created_at,
        completed_at=report.completed_at,
        freshness=FreshnessInfo(
            data_source="generated",
            last_updated_at=report.completed_at or report.created_at,
            cache_updated_at=None,
            is_stale=report.status in {ReportStatus.QUEUED, ReportStatus.RUNNING},
            refresh_scheduled=False,
        ),
    )


@router.post("/generate", response_model=ReportGenerateResponse)
def generate_report(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: ReportGenerateRequest,
) -> ReportGenerateResponse:
    try:
        report_request = ReportRequest(
            scope_type=ReportScopeType(payload.scope_type),
            scope_id=payload.scope_id,
            report_type=ReportType(payload.report_type),
            title=payload.title,
        )
    except ValueError as exc:
        return error_response(400, "invalid_report_scope", str(exc))

    try:
        service = get_report_service(request)
        queued_report = service.queue_report(report_request)
        if get_runtime(request).settings.reports_enabled:
            background_tasks.add_task(service.generate_existing_report, queued_report.id)
        return ReportGenerateResponse(
            id=queued_report.id,
            status=queued_report.status.value,
            scope_type=queued_report.scope_type.value,
            scope_id=queued_report.scope_id,
            created_at=queued_report.created_at,
        )
    except Exception as exc:
        return error_response(500, "report_generation_failed", str(exc))
