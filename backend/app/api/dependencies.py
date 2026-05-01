from __future__ import annotations

from fastapi import Request

from app.adapters.llm import LLMAdapter, NullLLMAdapter
from app.adapters.search import NullSearchAdapter, SearchAdapter
from app.services.chat import ChatService
from app.services.dashboard import DashboardService
from app.services.imports.service import CSVImportService
from app.services.map import MapService
from app.services.products import ProductService
from app.services.reports import ReportService
from app.services.runtime import RuntimeServices


def get_runtime(request: Request) -> RuntimeServices:
    runtime = request.app.state.runtime
    if runtime is None or not isinstance(runtime, RuntimeServices):
        raise RuntimeError("Application runtime is not initialized.")
    return runtime


def get_search_adapter(request: Request) -> SearchAdapter:
    adapter = getattr(request.app.state, "search_adapter", None)
    if isinstance(adapter, SearchAdapter):
        return adapter
    return NullSearchAdapter()


def get_llm_adapter(request: Request) -> LLMAdapter:
    adapter = getattr(request.app.state, "llm_adapter", None)
    if isinstance(adapter, LLMAdapter):
        return adapter
    return NullLLMAdapter()


def get_dashboard_service(request: Request) -> DashboardService:
    runtime = get_runtime(request)
    return DashboardService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
        search_adapter=get_search_adapter(request),
    )


def get_map_service(request: Request) -> MapService:
    runtime = get_runtime(request)
    return MapService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
        search_adapter=get_search_adapter(request),
    )


def get_product_service(request: Request) -> ProductService:
    runtime = get_runtime(request)
    return ProductService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
        search_adapter=get_search_adapter(request),
    )


def get_chat_service(request: Request) -> ChatService:
    runtime = get_runtime(request)
    return ChatService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
        llm_adapter=get_llm_adapter(request),
        search_adapter=get_search_adapter(request),
    )


def get_report_service(request: Request) -> ReportService:
    runtime = get_runtime(request)
    return ReportService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
        search_adapter=get_search_adapter(request),
    )


def get_import_service(request: Request) -> CSVImportService:
    runtime = get_runtime(request)
    return CSVImportService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
    )
