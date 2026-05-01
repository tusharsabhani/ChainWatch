from __future__ import annotations

import csv
from pathlib import Path

from app.db.repositories.catalog_repository import CatalogRepository
from app.db.repositories.import_repository import ImportRepository
from app.db.repositories.system_repository import SystemRepository
from app.schemas.imports import ImportStatus, ImportType
from app.services.imports.service import CSVImportService


def _write_csv(destination: Path, rows: list[dict[str, object]]) -> Path:
    fieldnames = list(rows[0].keys())
    with destination.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return destination


def test_supplier_import_persists_rows_and_artifacts(runtime, tmp_path: Path) -> None:
    service = CSVImportService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
    )
    source_path = _write_csv(
        tmp_path / "suppliers.csv",
        [
            {
                "supplier_code": "SUP-001",
                "name": "Atlas Supply",
                "country_code": "IN",
                "region": "APAC",
                "lead_time_days": 14,
                "reliability_score": 91.5,
                "active": 1,
            }
        ],
    )

    result = service.import_csv(ImportType.SUPPLIERS, source_path)

    assert result.status == ImportStatus.COMPLETED
    assert result.row_count == 1
    assert result.inserted_count == 1
    assert Path(runtime.settings.repo_root / result.raw_path).exists()
    assert Path(runtime.settings.repo_root / result.processed_summary_path).exists()

    catalog_repository = CatalogRepository(runtime.database)
    supplier = catalog_repository.get_supplier_by_code("SUP-001")
    assert supplier is not None
    assert supplier.name == "Atlas Supply"

    imports_repository = ImportRepository(runtime.database)
    import_row = imports_repository.get_import_run_row(result.id)
    assert import_row is not None
    assert import_row["status"] == "completed"
    assert import_row["inserted_count"] == 1


def test_product_import_creates_product_and_supplier_links(runtime, tmp_path: Path) -> None:
    service = CSVImportService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
    )

    supplier_csv = _write_csv(
        tmp_path / "suppliers.csv",
        [
            {
                "supplier_code": "SUP-PRIMARY",
                "name": "Primary Parts",
                "country_code": "US",
                "region": "NA",
                "lead_time_days": 7,
                "reliability_score": 96.0,
                "active": 1,
            },
            {
                "supplier_code": "SUP-BACKUP",
                "name": "Backup Parts",
                "country_code": "MX",
                "region": "LATAM",
                "lead_time_days": 10,
                "reliability_score": 88.0,
                "active": 1,
            },
        ],
    )
    service.import_csv(ImportType.SUPPLIERS, supplier_csv)

    product_csv = _write_csv(
        tmp_path / "products.csv",
        [
            {
                "sku": "SKU-200",
                "name": "Route Tracker",
                "category": "Electronics",
                "brand": "ChainWatch Demo",
                "status": "active",
                "origin_country_code": "US",
                "default_supplier_code": "SUP-PRIMARY",
                "alternate_supplier_codes": "SUP-BACKUP",
            }
        ],
    )

    result = service.import_csv(ImportType.PRODUCTS, product_csv)

    assert result.status == ImportStatus.COMPLETED

    catalog_repository = CatalogRepository(runtime.database)
    product = catalog_repository.get_product_by_sku("SKU-200")
    backup_supplier = catalog_repository.get_supplier_by_code("SUP-BACKUP")
    assert product is not None
    assert backup_supplier is not None
    assert product.default_supplier_id is not None
    assert catalog_repository.list_product_supplier_ids(product.id) == [
        product.default_supplier_id,
        backup_supplier.id,
    ]


def test_failed_import_returns_row_count_and_error_summary(runtime, tmp_path: Path) -> None:
    service = CSVImportService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
    )

    invalid_sales_csv = _write_csv(
        tmp_path / "sales.csv",
        [
            {
                "product_sku": "UNKNOWN-SKU",
                "sales_date": "2026-05-01",
                "channel": "web",
                "region_code": "NA",
                "units_sold": 10,
                "gross_revenue": 1000,
                "net_revenue": 950,
                "returns_qty": 0,
                "promo_flag": 0,
                "stockout_flag": 0,
            }
        ],
    )

    result = service.import_csv(ImportType.SALES, invalid_sales_csv)

    assert result.status == ImportStatus.FAILED
    assert result.row_count == 1
    assert result.inserted_count == 0
    assert result.error_count == 1
    assert result.errors[0].field == "product_sku"

    system_repository = SystemRepository(runtime.database)
    assert system_repository.count_rows("sales_history") == 0


def test_inventory_and_fulfillment_imports_write_normalized_rows(runtime, tmp_path: Path) -> None:
    service = CSVImportService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
    )

    supplier_csv = _write_csv(
        tmp_path / "suppliers.csv",
        [
            {
                "supplier_code": "SUP-001",
                "name": "Atlas Supply",
                "country_code": "IN",
                "region": "APAC",
                "lead_time_days": 14,
                "reliability_score": 91.5,
                "active": 1,
            }
        ],
    )
    product_csv = _write_csv(
        tmp_path / "products.csv",
        [
            {
                "sku": "SKU-300",
                "name": "Dock Sensor",
                "category": "Sensors",
                "brand": "ChainWatch Demo",
                "status": "active",
                "origin_country_code": "IN",
                "default_supplier_code": "SUP-001",
                "alternate_supplier_codes": "",
            }
        ],
    )
    inventory_csv = _write_csv(
        tmp_path / "inventory.csv",
        [
            {
                "product_sku": "SKU-300",
                "warehouse_code": "WH-01",
                "snapshot_date": "2026-05-01T08:00:00+00:00",
                "on_hand_qty": 50,
                "reserved_qty": 5,
                "inbound_qty": 20,
                "reorder_point": 25,
                "safety_stock": 10,
                "days_of_cover": 12.5,
            }
        ],
    )
    fulfillment_csv = _write_csv(
        tmp_path / "fulfillment.csv",
        [
            {
                "product_sku": "SKU-300",
                "region_code": "APAC",
                "warehouse_code": "WH-01",
                "captured_at": "2026-05-01T09:00:00+00:00",
                "backlog_orders": 8,
                "avg_ship_delay_hours": 4.0,
                "on_time_rate": 0.97,
                "sla_risk_level": 2,
            }
        ],
    )

    service.import_csv(ImportType.SUPPLIERS, supplier_csv)
    service.import_csv(ImportType.PRODUCTS, product_csv)
    inventory_result = service.import_csv(ImportType.INVENTORY, inventory_csv)
    fulfillment_result = service.import_csv(ImportType.FULFILLMENT, fulfillment_csv)

    assert inventory_result.status == ImportStatus.COMPLETED
    assert fulfillment_result.status == ImportStatus.COMPLETED

    system_repository = SystemRepository(runtime.database)
    assert system_repository.count_rows("inventory_snapshots") == 1
    assert system_repository.count_rows("fulfillment_snapshots") == 1
