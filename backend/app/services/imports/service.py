from __future__ import annotations

import csv
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.config import Settings
from app.db.connection import SQLiteConnectionFactory
from app.db.repositories.catalog_repository import CatalogRepository
from app.db.repositories.data_repository import DataRepository
from app.db.repositories.import_repository import ImportRepository
from app.schemas.catalog import ProductCreate, ProductSupplierLink, SupplierCreate
from app.schemas.imports import ImportResult, ImportRowError, ImportStatus, ImportType
from app.services.storage import StorageManager

ALLOWED_PRODUCT_STATUSES = {"active", "inactive", "discontinued"}
ALLOWED_IMPORT_TYPES = {
    ImportType.PRODUCTS,
    ImportType.SUPPLIERS,
    ImportType.SALES,
    ImportType.INVENTORY,
    ImportType.FULFILLMENT,
}


def _normalize_cell(value: str | None) -> str:
    return (value or "").strip()


def _split_codes(value: str | None) -> list[str]:
    raw_value = _normalize_cell(value)
    if not raw_value:
        return []

    normalized = raw_value
    for delimiter in ("|", ";"):
        normalized = normalized.replace(delimiter, ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def _parse_iso_date(value: str, field_name: str) -> str:
    normalized = _normalize_cell(value)
    if not normalized:
        raise ValueError(f"{field_name} is required")

    try:
        if "T" in normalized or " " in normalized:
            datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        else:
            date.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO date/time") from exc
    return normalized


def _parse_int(value: str | None, field_name: str, *, minimum: int | None = None) -> int:
    normalized = _normalize_cell(value)
    if not normalized:
        raise ValueError(f"{field_name} is required")
    try:
        parsed = int(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an integer") from exc
    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    return parsed


def _parse_optional_int(value: str | None, field_name: str) -> int | None:
    normalized = _normalize_cell(value)
    if not normalized:
        return None
    try:
        return int(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an integer") from exc


def _parse_float(value: str | None, field_name: str, *, minimum: float | None = None) -> float:
    normalized = _normalize_cell(value)
    if not normalized:
        raise ValueError(f"{field_name} is required")
    try:
        parsed = float(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a number") from exc
    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    return parsed


def _parse_optional_float(value: str | None, field_name: str) -> float | None:
    normalized = _normalize_cell(value)
    if not normalized:
        return None
    try:
        return float(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a number") from exc


def _parse_bool_int(value: str | None, field_name: str) -> int:
    normalized = _normalize_cell(value).lower()
    if normalized in {"1", "true", "yes", "y"}:
        return 1
    if normalized in {"0", "false", "no", "n"}:
        return 0
    raise ValueError(f"{field_name} must be one of: 1, 0, true, false, yes, no")


def _parse_required_text(value: str | None, field_name: str) -> str:
    normalized = _normalize_cell(value)
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _build_error(row_number: int, field_name: str, message: str) -> ImportRowError:
    return ImportRowError(row_number=row_number, field=field_name, message=message)


@dataclass(slots=True)
class SupplierImportRow:
    supplier: SupplierCreate


@dataclass(slots=True)
class ProductImportRow:
    product: ProductCreate
    supplier_links: list[ProductSupplierLink]


@dataclass(slots=True)
class SalesImportRow:
    product_id: int
    sales_date: str
    channel: str
    region_code: str
    units_sold: int
    gross_revenue: float
    net_revenue: float
    returns_qty: int
    promo_flag: int
    stockout_flag: int


@dataclass(slots=True)
class InventoryImportRow:
    product_id: int
    warehouse_code: str
    snapshot_date: str
    on_hand_qty: int
    reserved_qty: int
    inbound_qty: int
    reorder_point: int
    safety_stock: int
    days_of_cover: float | None


@dataclass(slots=True)
class FulfillmentImportRow:
    product_id: int
    region_code: str
    warehouse_code: str | None
    captured_at: str
    backlog_orders: int
    avg_ship_delay_hours: float
    on_time_rate: float
    sla_risk_level: int


class CSVImportService:
    def __init__(
        self,
        *,
        settings: Settings,
        storage: StorageManager,
        database: SQLiteConnectionFactory,
    ) -> None:
        self.settings = settings
        self.storage = storage
        self.database = database
        self.catalog_repository = CatalogRepository(database)
        self.data_repository = DataRepository(database)
        self.import_repository = ImportRepository(database)

    def import_csv(self, import_type: ImportType, source_path: Path) -> ImportResult:
        if import_type not in ALLOWED_IMPORT_TYPES:
            raise ValueError(f"Unsupported import type: {import_type}")

        resolved_source = source_path.resolve()
        if not resolved_source.exists():
            raise FileNotFoundError(f"Import source does not exist: {resolved_source}")

        import_id = self._generate_import_id()
        started_at = self.import_repository.create_import_run(
            import_id=import_id,
            import_type=import_type,
            filename=resolved_source.name,
        )
        raw_path = self.storage.persist_raw_import(resolved_source, import_id)

        row_count = 0
        inserted_count = 0
        errors: list[ImportRowError] = []
        notes: str | None = None

        try:
            rows = self._read_csv_rows(resolved_source)
            row_count = len(rows)

            normalized_rows, errors = self._normalize_rows(import_type, rows)
            if errors:
                notes = self._summarize_errors(errors)
                completed_at = self.import_repository.finalize_import_run(
                    import_id=import_id,
                    status=ImportStatus.FAILED,
                    row_count=row_count,
                    inserted_count=0,
                    error_count=len(errors),
                    notes=notes,
                )
                processed_summary_path = self._write_processed_summary(
                    import_id=import_id,
                    import_type=import_type,
                    filename=resolved_source.name,
                    status=ImportStatus.FAILED,
                    row_count=row_count,
                    inserted_count=0,
                    started_at=started_at,
                    completed_at=completed_at,
                    notes=notes,
                    errors=errors,
                )
                return self._build_result(
                    import_id=import_id,
                    import_type=import_type,
                    filename=resolved_source.name,
                    status=ImportStatus.FAILED,
                    row_count=row_count,
                    inserted_count=0,
                    error_count=len(errors),
                    started_at=started_at,
                    completed_at=completed_at,
                    notes=notes,
                    errors=errors,
                    raw_path=raw_path,
                    processed_summary_path=processed_summary_path,
                )

            with self.database.transaction() as connection:
                inserted_count = self._persist_rows(import_type, normalized_rows, connection)

            notes = f"Imported {inserted_count} {import_type.value} row(s) successfully."
            completed_at = self.import_repository.finalize_import_run(
                import_id=import_id,
                status=ImportStatus.COMPLETED,
                row_count=row_count,
                inserted_count=inserted_count,
                error_count=0,
                notes=notes,
            )
            processed_summary_path = self._write_processed_summary(
                import_id=import_id,
                import_type=import_type,
                filename=resolved_source.name,
                status=ImportStatus.COMPLETED,
                row_count=row_count,
                inserted_count=inserted_count,
                started_at=started_at,
                completed_at=completed_at,
                notes=notes,
                errors=[],
            )
            return self._build_result(
                import_id=import_id,
                import_type=import_type,
                filename=resolved_source.name,
                status=ImportStatus.COMPLETED,
                row_count=row_count,
                inserted_count=inserted_count,
                error_count=0,
                started_at=started_at,
                completed_at=completed_at,
                notes=notes,
                errors=[],
                raw_path=raw_path,
                processed_summary_path=processed_summary_path,
            )
        except Exception as exc:
            notes = f"Import failed: {exc}"
            completed_at = self.import_repository.finalize_import_run(
                import_id=import_id,
                status=ImportStatus.FAILED,
                row_count=row_count,
                inserted_count=0,
                error_count=max(1, len(errors)),
                notes=notes,
            )
            processed_summary_path = self._write_processed_summary(
                import_id=import_id,
                import_type=import_type,
                filename=resolved_source.name,
                status=ImportStatus.FAILED,
                row_count=row_count,
                inserted_count=0,
                started_at=started_at,
                completed_at=completed_at,
                notes=notes,
                errors=errors or [_build_error(0, "_import", str(exc))],
            )
            return self._build_result(
                import_id=import_id,
                import_type=import_type,
                filename=resolved_source.name,
                status=ImportStatus.FAILED,
                row_count=row_count,
                inserted_count=0,
                error_count=max(1, len(errors)),
                started_at=started_at,
                completed_at=completed_at,
                notes=notes,
                errors=errors or [_build_error(0, "_import", str(exc))],
                raw_path=raw_path,
                processed_summary_path=processed_summary_path,
            )

    def _read_csv_rows(self, source_path: Path) -> list[dict[str, str]]:
        with source_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            if reader.fieldnames is None:
                raise ValueError("CSV file is missing a header row")
            return [
                {key: value or "" for key, value in row.items()}
                for row in reader
            ]

    def _normalize_rows(
        self,
        import_type: ImportType,
        rows: list[dict[str, str]],
    ) -> tuple[list[Any], list[ImportRowError]]:
        errors: list[ImportRowError] = []
        normalized_rows: list[Any] = []

        for row_number, row in enumerate(rows, start=2):
            try:
                normalized_rows.append(self._normalize_row(import_type, row))
            except ValueError as exc:
                field_name, message = self._split_validation_message(str(exc))
                errors.append(_build_error(row_number, field_name, message))

        return normalized_rows, errors

    def _normalize_row(self, import_type: ImportType, row: dict[str, str]) -> Any:
        if import_type == ImportType.SUPPLIERS:
            return self._normalize_supplier_row(row)
        if import_type == ImportType.PRODUCTS:
            return self._normalize_product_row(row)
        if import_type == ImportType.SALES:
            return self._normalize_sales_row(row)
        if import_type == ImportType.INVENTORY:
            return self._normalize_inventory_row(row)
        if import_type == ImportType.FULFILLMENT:
            return self._normalize_fulfillment_row(row)
        raise ValueError(f"_import: Unsupported import type {import_type}")

    def _normalize_supplier_row(self, row: dict[str, str]) -> SupplierImportRow:
        supplier = SupplierCreate(
            supplier_code=_parse_required_text(row.get("supplier_code"), "supplier_code"),
            name=_parse_required_text(row.get("name"), "name"),
            country_code=_parse_required_text(row.get("country_code"), "country_code"),
            region=_normalize_cell(row.get("region")) or None,
            lead_time_days=_parse_optional_int(row.get("lead_time_days"), "lead_time_days"),
            reliability_score=_parse_optional_float(
                row.get("reliability_score"),
                "reliability_score",
            ),
            active=_parse_bool_int(row.get("active"), "active"),
        )
        return SupplierImportRow(supplier=supplier)

    def _normalize_product_row(self, row: dict[str, str]) -> ProductImportRow:
        sku = _parse_required_text(row.get("sku"), "sku")
        default_supplier_code = _normalize_cell(row.get("default_supplier_code"))
        alternate_supplier_codes = _split_codes(row.get("alternate_supplier_codes"))
        status = _parse_required_text(row.get("status"), "status").lower()

        if status not in ALLOWED_PRODUCT_STATUSES:
            raise ValueError("status: status must be active, inactive, or discontinued")

        default_supplier_id: int | None = None
        supplier_links: list[ProductSupplierLink] = []

        if default_supplier_code:
            default_supplier = self.catalog_repository.get_supplier_by_code(default_supplier_code)
            if default_supplier is None:
                raise ValueError(
                    f"default_supplier_code: unknown supplier code {default_supplier_code}"
                )
            default_supplier_id = default_supplier.id
            supplier_links.append(
                ProductSupplierLink(
                    supplier_id=default_supplier.id,
                    is_primary=1,
                )
            )

        if alternate_supplier_codes and default_supplier_id is None:
            raise ValueError(
                "alternate_supplier_codes: default_supplier_code is required when alternate supplier codes are provided"
            )

        seen_supplier_ids = {default_supplier_id} if default_supplier_id is not None else set()
        for supplier_code in alternate_supplier_codes:
            supplier = self.catalog_repository.get_supplier_by_code(supplier_code)
            if supplier is None:
                raise ValueError(
                    f"alternate_supplier_codes: unknown supplier code {supplier_code}"
                )
            if supplier.id in seen_supplier_ids:
                continue
            seen_supplier_ids.add(supplier.id)
            supplier_links.append(
                ProductSupplierLink(
                    supplier_id=supplier.id,
                    is_primary=0,
                )
            )

        product = ProductCreate(
            sku=sku,
            name=_parse_required_text(row.get("name"), "name"),
            category=_parse_required_text(row.get("category"), "category"),
            brand=_normalize_cell(row.get("brand")) or None,
            status=status,
            default_supplier_id=default_supplier_id,
            origin_country_code=_normalize_cell(row.get("origin_country_code")) or None,
        )
        return ProductImportRow(product=product, supplier_links=supplier_links)

    def _normalize_sales_row(self, row: dict[str, str]) -> SalesImportRow:
        product_sku = _parse_required_text(row.get("product_sku"), "product_sku")
        product = self.catalog_repository.get_product_by_sku(product_sku)
        if product is None:
            raise ValueError(f"product_sku: unknown product sku {product_sku}")

        return SalesImportRow(
            product_id=product.id,
            sales_date=_parse_iso_date(row.get("sales_date", ""), "sales_date"),
            channel=_parse_required_text(row.get("channel"), "channel"),
            region_code=_parse_required_text(row.get("region_code"), "region_code"),
            units_sold=_parse_int(row.get("units_sold"), "units_sold", minimum=0),
            gross_revenue=_parse_float(row.get("gross_revenue"), "gross_revenue", minimum=0),
            net_revenue=_parse_float(row.get("net_revenue"), "net_revenue", minimum=0),
            returns_qty=_parse_int(row.get("returns_qty"), "returns_qty", minimum=0),
            promo_flag=_parse_bool_int(row.get("promo_flag"), "promo_flag"),
            stockout_flag=_parse_bool_int(row.get("stockout_flag"), "stockout_flag"),
        )

    def _normalize_inventory_row(self, row: dict[str, str]) -> InventoryImportRow:
        product_sku = _parse_required_text(row.get("product_sku"), "product_sku")
        product = self.catalog_repository.get_product_by_sku(product_sku)
        if product is None:
            raise ValueError(f"product_sku: unknown product sku {product_sku}")

        return InventoryImportRow(
            product_id=product.id,
            warehouse_code=_parse_required_text(row.get("warehouse_code"), "warehouse_code"),
            snapshot_date=_parse_iso_date(row.get("snapshot_date", ""), "snapshot_date"),
            on_hand_qty=_parse_int(row.get("on_hand_qty"), "on_hand_qty", minimum=0),
            reserved_qty=_parse_int(row.get("reserved_qty"), "reserved_qty", minimum=0),
            inbound_qty=_parse_int(row.get("inbound_qty"), "inbound_qty", minimum=0),
            reorder_point=_parse_int(row.get("reorder_point"), "reorder_point", minimum=0),
            safety_stock=_parse_int(row.get("safety_stock"), "safety_stock", minimum=0),
            days_of_cover=_parse_optional_float(row.get("days_of_cover"), "days_of_cover"),
        )

    def _normalize_fulfillment_row(self, row: dict[str, str]) -> FulfillmentImportRow:
        product_sku = _parse_required_text(row.get("product_sku"), "product_sku")
        product = self.catalog_repository.get_product_by_sku(product_sku)
        if product is None:
            raise ValueError(f"product_sku: unknown product sku {product_sku}")

        on_time_rate = _parse_float(row.get("on_time_rate"), "on_time_rate", minimum=0)
        if on_time_rate > 1:
            raise ValueError("on_time_rate: on_time_rate must be between 0 and 1")

        sla_risk_level = _parse_int(row.get("sla_risk_level"), "sla_risk_level", minimum=1)
        if sla_risk_level > 5:
            raise ValueError("sla_risk_level: sla_risk_level must be between 1 and 5")

        return FulfillmentImportRow(
            product_id=product.id,
            region_code=_parse_required_text(row.get("region_code"), "region_code"),
            warehouse_code=_normalize_cell(row.get("warehouse_code")) or None,
            captured_at=_parse_iso_date(row.get("captured_at", ""), "captured_at"),
            backlog_orders=_parse_int(row.get("backlog_orders"), "backlog_orders", minimum=0),
            avg_ship_delay_hours=_parse_float(
                row.get("avg_ship_delay_hours"),
                "avg_ship_delay_hours",
                minimum=0,
            ),
            on_time_rate=on_time_rate,
            sla_risk_level=sla_risk_level,
        )

    def _persist_rows(
        self,
        import_type: ImportType,
        normalized_rows: list[Any],
        connection: sqlite3.Connection,
    ) -> int:
        inserted_count = 0
        for normalized_row in normalized_rows:
            if import_type == ImportType.SUPPLIERS:
                self.catalog_repository.upsert_supplier(
                    normalized_row.supplier,
                    connection=connection,
                )
            elif import_type == ImportType.PRODUCTS:
                product_id = self.catalog_repository.upsert_product(
                    normalized_row.product,
                    connection=connection,
                )
                self.catalog_repository.replace_product_suppliers(
                    product_id,
                    normalized_row.supplier_links,
                    connection=connection,
                )
            elif import_type == ImportType.SALES:
                self.data_repository.replace_sales_history_row(
                    product_id=normalized_row.product_id,
                    sales_date=normalized_row.sales_date,
                    channel=normalized_row.channel,
                    region_code=normalized_row.region_code,
                    units_sold=normalized_row.units_sold,
                    gross_revenue=normalized_row.gross_revenue,
                    net_revenue=normalized_row.net_revenue,
                    returns_qty=normalized_row.returns_qty,
                    promo_flag=normalized_row.promo_flag,
                    stockout_flag=normalized_row.stockout_flag,
                    connection=connection,
                )
            elif import_type == ImportType.INVENTORY:
                self.data_repository.replace_inventory_snapshot_row(
                    product_id=normalized_row.product_id,
                    warehouse_code=normalized_row.warehouse_code,
                    snapshot_date=normalized_row.snapshot_date,
                    on_hand_qty=normalized_row.on_hand_qty,
                    reserved_qty=normalized_row.reserved_qty,
                    inbound_qty=normalized_row.inbound_qty,
                    reorder_point=normalized_row.reorder_point,
                    safety_stock=normalized_row.safety_stock,
                    days_of_cover=normalized_row.days_of_cover,
                    connection=connection,
                )
            elif import_type == ImportType.FULFILLMENT:
                self.data_repository.replace_fulfillment_snapshot_row(
                    product_id=normalized_row.product_id,
                    region_code=normalized_row.region_code,
                    warehouse_code=normalized_row.warehouse_code,
                    captured_at=normalized_row.captured_at,
                    backlog_orders=normalized_row.backlog_orders,
                    avg_ship_delay_hours=normalized_row.avg_ship_delay_hours,
                    on_time_rate=normalized_row.on_time_rate,
                    sla_risk_level=normalized_row.sla_risk_level,
                    connection=connection,
                )
            else:
                raise ValueError(f"Unsupported import type: {import_type}")
            inserted_count += 1
        return inserted_count

    def _write_processed_summary(
        self,
        *,
        import_id: str,
        import_type: ImportType,
        filename: str,
        status: ImportStatus,
        row_count: int,
        inserted_count: int,
        started_at: str,
        completed_at: str,
        notes: str | None,
        errors: list[ImportRowError],
    ) -> Path:
        payload = {
            "id": import_id,
            "importType": import_type.value,
            "filename": filename,
            "status": status.value,
            "rowCount": row_count,
            "insertedCount": inserted_count,
            "errorCount": len(errors),
            "startedAt": started_at,
            "completedAt": completed_at,
            "notes": notes,
            "errors": [error.model_dump(mode="json") for error in errors],
        }
        return self.storage.write_import_processed_summary(import_id, payload)

    def _build_result(
        self,
        *,
        import_id: str,
        import_type: ImportType,
        filename: str,
        status: ImportStatus,
        row_count: int,
        inserted_count: int,
        error_count: int,
        started_at: str,
        completed_at: str,
        notes: str | None,
        errors: list[ImportRowError],
        raw_path: Path,
        processed_summary_path: Path,
    ) -> ImportResult:
        return ImportResult(
            id=import_id,
            import_type=import_type,
            filename=filename,
            status=status,
            row_count=row_count,
            inserted_count=inserted_count,
            error_count=error_count,
            started_at=started_at,
            completed_at=completed_at,
            notes=notes,
            errors=errors,
            raw_path=self.settings.to_relative_path(raw_path),
            processed_summary_path=self.settings.to_relative_path(processed_summary_path),
        )

    def _summarize_errors(self, errors: list[ImportRowError]) -> str:
        first_error = errors[0]
        if len(errors) == 1:
            return (
                f"Import failed with 1 validation error: row {first_error.row_number} "
                f"{first_error.field} {first_error.message}"
            )
        return (
            f"Import failed with {len(errors)} validation errors. "
            f"First error: row {first_error.row_number} {first_error.field} {first_error.message}"
        )

    def _split_validation_message(self, message: str) -> tuple[str, str]:
        if ": " not in message:
            return ("_row", message)
        field_name, detail = message.split(": ", 1)
        return field_name, detail

    def _generate_import_id(self) -> str:
        return f"imp_{uuid.uuid4().hex[:12]}"
