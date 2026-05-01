from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query, Request

from app.api.dependencies import get_dashboard_service
from app.api.errors import error_response
from app.schemas.dashboard import DashboardAlertsResponse, DashboardSummaryResponse

router = APIRouter(prefix="/dashboard")


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    request: Request,
    date_range: Literal["7d", "30d", "90d"] = Query(default="30d"),
    severity_min: int = Query(default=3, ge=1, le=5),
    category: str | None = None,
    region: str | None = None,
) -> DashboardSummaryResponse:
    try:
        service = get_dashboard_service(request)
        return service.get_summary(
            date_range=date_range,
            severity_min=severity_min,
            category=category,
            region=region,
        )
    except ValueError as exc:
        return error_response(400, "invalid_filter", str(exc))
    except Exception as exc:
        return error_response(500, "dashboard_summary_unavailable", str(exc))


@router.get("/alerts", response_model=DashboardAlertsResponse)
def get_dashboard_alerts(
    request: Request,
    severity_min: int = Query(default=1, ge=1, le=5),
    status: Literal["open", "monitoring", "resolved"] | None = None,
    limit: int = Query(default=25, ge=1, le=100),
) -> DashboardAlertsResponse:
    try:
        service = get_dashboard_service(request)
        return service.get_alerts(
            severity_min=severity_min,
            status=status,
            limit=limit,
        )
    except Exception as exc:
        return error_response(500, "dashboard_alerts_unavailable", str(exc))
