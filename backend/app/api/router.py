from fastapi import APIRouter

from app.api.routes.chat import router as chat_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router
from app.api.routes.imports import router as imports_router
from app.api.routes.map import router as map_router
from app.api.routes.products import router as products_router
from app.api.routes.reports import router as reports_router

api_router = APIRouter()
api_router.include_router(dashboard_router, tags=["dashboard"])
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(health_router, tags=["health"])
api_router.include_router(map_router, tags=["map"])
api_router.include_router(products_router, tags=["products"])
api_router.include_router(reports_router, tags=["reports"])
api_router.include_router(imports_router, tags=["imports"])
