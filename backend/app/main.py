from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.adapters.llm import LLMAdapter, build_llm_adapter
from app.adapters.search import SearchAdapter, build_search_adapter
from app.api.router import api_router
from app.config import Settings, get_settings
from app.services.runtime import RuntimeServices, bootstrap_runtime


def create_app(
    settings: Settings | None = None,
    *,
    llm_adapter: LLMAdapter | None = None,
    search_adapter: SearchAdapter | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    resolved_llm_adapter = llm_adapter or build_llm_adapter(resolved_settings)
    resolved_search_adapter = search_adapter or build_search_adapter(resolved_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        runtime = bootstrap_runtime(resolved_settings)
        app.state.settings = resolved_settings
        app.state.runtime = runtime
        app.state.llm_adapter = resolved_llm_adapter
        app.state.search_adapter = resolved_search_adapter
        yield

    app = FastAPI(
        title=resolved_settings.app_name,
        version=resolved_settings.app_version,
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.state.runtime = None
    app.state.llm_adapter = resolved_llm_adapter
    app.state.search_adapter = resolved_search_adapter
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
