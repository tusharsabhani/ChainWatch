from __future__ import annotations

from app.db.repositories.system_repository import SystemRepository
from app.schemas.health import (
    BackgroundTaskHealth,
    DatabaseHealth,
    HealthResponse,
    ProviderHealth,
    StorageHealth,
)
from app.services.runtime import RuntimeServices


def build_health_response(runtime: RuntimeServices) -> HealthResponse:
    system_repository = SystemRepository(runtime.database)

    database_status = "connected" if system_repository.ping() else "disconnected"
    overall_status = "ok" if database_status == "connected" else "degraded"

    settings = runtime.settings

    return HealthResponse(
        status=overall_status,
        app_version=settings.app_version,
        database=DatabaseHealth(
            status=database_status,
            path=settings.to_relative_path(settings.database_path),
        ),
        storage=StorageHealth(
            reports_json_path=settings.to_relative_path(settings.reports_json_dir),
            reports_markdown_path=settings.to_relative_path(settings.reports_markdown_dir),
            imports_path=settings.to_relative_path(settings.imports_raw_dir),
            cache_path=settings.to_relative_path(settings.cache_external_risk_dir),
        ),
        providers=ProviderHealth(
            llm_configured=settings.llm_configured,
            search_configured=settings.search_configured,
        ),
        background_tasks=BackgroundTaskHealth(
            reports_enabled=settings.reports_enabled,
            external_risk_refresh_enabled=settings.external_risk_refresh_enabled,
        ),
    )

