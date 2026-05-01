from __future__ import annotations

from app.schemas.common import CamelModel


class DatabaseHealth(CamelModel):
    status: str
    path: str


class StorageHealth(CamelModel):
    reports_json_path: str
    reports_markdown_path: str
    imports_path: str
    cache_path: str


class ProviderHealth(CamelModel):
    llm_configured: bool
    search_configured: bool


class BackgroundTaskHealth(CamelModel):
    reports_enabled: bool
    external_risk_refresh_enabled: bool


class HealthResponse(CamelModel):
    status: str
    app_version: str
    database: DatabaseHealth
    storage: StorageHealth
    providers: ProviderHealth
    background_tasks: BackgroundTaskHealth
