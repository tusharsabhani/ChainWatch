from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Query, Request

from app.api.dependencies import get_map_service
from app.api.errors import error_response
from app.schemas.map import CountryDetailResponse, MapCountriesResponse

router = APIRouter(prefix="/map")


@router.get("/countries", response_model=MapCountriesResponse)
def get_map_countries(
    request: Request,
    background_tasks: BackgroundTasks,
    risk_type: str | None = None,
    severity_min: int = Query(default=1, ge=1, le=5),
) -> MapCountriesResponse:
    try:
        service = get_map_service(request)
        return service.list_countries(
            risk_type=risk_type,
            severity_min=severity_min,
            background_tasks=background_tasks,
        )
    except Exception as exc:
        return error_response(500, "country_scores_unavailable", str(exc))


@router.get("/countries/{country_code}", response_model=CountryDetailResponse)
def get_country_detail(
    request: Request,
    background_tasks: BackgroundTasks,
    country_code: str,
) -> CountryDetailResponse:
    try:
        service = get_map_service(request)
        return service.get_country_detail(country_code, background_tasks=background_tasks)
    except LookupError as exc:
        return error_response(404, "country_not_found", str(exc))
    except Exception as exc:
        return error_response(500, "country_detail_unavailable", str(exc))
