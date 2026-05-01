from __future__ import annotations

from fastapi import APIRouter, Request

from app.schemas.health import HealthResponse
from app.services.health import build_health_response
from app.services.runtime import RuntimeServices

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health(request: Request) -> HealthResponse:
    runtime = request.app.state.runtime
    if runtime is None or not isinstance(runtime, RuntimeServices):
        raise RuntimeError("Application runtime is not initialized.")
    return build_health_response(runtime)

