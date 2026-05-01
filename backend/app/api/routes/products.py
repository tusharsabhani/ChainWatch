from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Query, Request

from app.api.dependencies import get_product_service
from app.api.errors import error_response
from app.schemas.products import ProductDetailResponse, ProductListResponse

router = APIRouter(prefix="/products")


@router.get("", response_model=ProductListResponse)
def get_products(
    request: Request,
    query: str | None = None,
    category: str | None = None,
    risk_min: float | None = Query(default=None, ge=1.0, le=5.0),
    limit: int = Query(default=25, ge=1, le=100),
) -> ProductListResponse:
    try:
        service = get_product_service(request)
        return service.list_products(
            query=query,
            category=category,
            risk_min=risk_min,
            limit=limit,
        )
    except Exception as exc:
        return error_response(500, "products_unavailable", str(exc))


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product_detail(
    request: Request,
    background_tasks: BackgroundTasks,
    product_id: int,
    date_range: Literal["30d", "90d", "365d"] = Query(default="90d"),
    region: str | None = None,
    channel: str | None = None,
) -> ProductDetailResponse:
    try:
        service = get_product_service(request)
        return service.get_product_detail(
            product_id=product_id,
            date_range=date_range,
            region=region,
            channel=channel,
            background_tasks=background_tasks,
        )
    except LookupError as exc:
        return error_response(404, "product_not_found", str(exc))
    except Exception as exc:
        return error_response(500, "product_detail_unavailable", str(exc))
