from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class ErrorDetail(CamelModel):
    code: str
    message: str
    details: dict[str, object] = Field(default_factory=dict)


class ErrorResponse(CamelModel):
    error: ErrorDetail

