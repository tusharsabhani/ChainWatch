from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.config import Settings, get_settings
from app.services.runtime import RuntimeServices, bootstrap_runtime


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        runtime = bootstrap_runtime(resolved_settings)
        app.state.settings = resolved_settings
        app.state.runtime = runtime
        yield

    app = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.state.runtime = None
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()

