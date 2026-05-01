from __future__ import annotations

from app.schemas.common import CamelModel


class ImportListItem(CamelModel):
    id: str
    import_type: str
    filename: str
    status: str
    row_count: int
    inserted_count: int
    error_count: int
    completed_at: str | None = None


class ImportsListResponse(CamelModel):
    items: list[ImportListItem]


class ImportStartRequest(CamelModel):
    file_path: str


class ImportStartResponse(CamelModel):
    id: str
    import_type: str
    status: str
