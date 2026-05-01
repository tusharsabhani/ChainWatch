from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request

from app.api.dependencies import get_import_service, get_runtime
from app.api.errors import error_response
from app.db.repositories.import_repository import ImportRepository
from app.schemas.imports import ImportType
from app.schemas.imports_api import ImportListItem, ImportsListResponse, ImportStartRequest, ImportStartResponse

router = APIRouter(prefix="/imports")


@router.get("", response_model=ImportsListResponse)
def get_imports(request: Request) -> ImportsListResponse:
    try:
        runtime = get_runtime(request)
        repository = ImportRepository(runtime.database)
        rows = repository.list_import_runs()
        return ImportsListResponse(
            items=[
                ImportListItem(
                    id=str(row["id"]),
                    import_type=str(row["import_type"]),
                    filename=str(row["filename"]),
                    status=str(row["status"]),
                    row_count=int(row["row_count"]),
                    inserted_count=int(row["inserted_count"]),
                    error_count=int(row["error_count"]),
                    completed_at=str(row["completed_at"]) if row["completed_at"] is not None else None,
                )
                for row in rows
            ]
        )
    except Exception as exc:
        return error_response(500, "imports_unavailable", str(exc))


def _run_import(request: Request, import_type: ImportType, payload: ImportStartRequest) -> ImportStartResponse:
    try:
        source_path = Path(payload.file_path).expanduser().resolve()
    except Exception as exc:
        return error_response(400, "invalid_import_file", str(exc))

    try:
        service = get_import_service(request)
        result = service.import_csv(import_type, source_path)
        return ImportStartResponse(
            id=result.id,
            import_type=result.import_type.value,
            status=result.status.value,
        )
    except (FileNotFoundError, ValueError) as exc:
        return error_response(400, "invalid_import_file", str(exc))
    except Exception as exc:
        error_codes = {
            ImportType.PRODUCTS: "product_import_failed",
            ImportType.SALES: "sales_import_failed",
            ImportType.INVENTORY: "inventory_import_failed",
            ImportType.SUPPLIERS: "supplier_import_failed",
            ImportType.FULFILLMENT: "fulfillment_import_failed",
        }
        return error_response(500, error_codes[import_type], str(exc))


@router.post("/products", response_model=ImportStartResponse)
def import_products(request: Request, payload: ImportStartRequest) -> ImportStartResponse:
    return _run_import(request, ImportType.PRODUCTS, payload)


@router.post("/sales", response_model=ImportStartResponse)
def import_sales(request: Request, payload: ImportStartRequest) -> ImportStartResponse:
    return _run_import(request, ImportType.SALES, payload)


@router.post("/inventory", response_model=ImportStartResponse)
def import_inventory(request: Request, payload: ImportStartRequest) -> ImportStartResponse:
    return _run_import(request, ImportType.INVENTORY, payload)


@router.post("/suppliers", response_model=ImportStartResponse)
def import_suppliers(request: Request, payload: ImportStartRequest) -> ImportStartResponse:
    return _run_import(request, ImportType.SUPPLIERS, payload)
