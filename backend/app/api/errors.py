from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from app.schemas.common import ErrorDetail, ErrorResponse


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details or {},
        )
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json", by_alias=True),
    )

