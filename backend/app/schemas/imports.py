from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ImportType(StrEnum):
    PRODUCTS = "products"
    SUPPLIERS = "suppliers"
    SALES = "sales"
    INVENTORY = "inventory"
    FULFILLMENT = "fulfillment"


class ImportStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImportRowError(BaseModel):
    row_number: int
    field: str
    message: str


class ImportResult(BaseModel):
    id: str
    import_type: ImportType
    filename: str
    status: ImportStatus
    row_count: int
    inserted_count: int
    error_count: int
    started_at: str
    completed_at: str | None = None
    notes: str | None = None
    errors: list[ImportRowError] = Field(default_factory=list)
    raw_path: str
    processed_summary_path: str


class SeedRunResult(BaseModel):
    import_results: list[ImportResult]
