from __future__ import annotations

import csv
import tempfile
from datetime import date, timedelta
from pathlib import Path

from app.config import Settings
from app.db.connection import SQLiteConnectionFactory
from app.schemas.imports import ImportType, SeedRunResult
from app.services.imports.service import CSVImportService
from app.services.storage import StorageManager


class DemoSeedService:
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
        self.import_service = CSVImportService(
            settings=settings,
            storage=storage,
            database=database,
        )

    def seed_demo_data(self) -> SeedRunResult:
        with tempfile.TemporaryDirectory(prefix="chainwatch-seed-") as temp_dir:
            temp_path = Path(temp_dir)

            results = [
                self.import_service.import_csv(
                    ImportType.SUPPLIERS,
                    self._write_csv(temp_path / "suppliers.csv", self._supplier_rows()),
                ),
                self.import_service.import_csv(
                    ImportType.PRODUCTS,
                    self._write_csv(temp_path / "products.csv", self._product_rows()),
                ),
                self.import_service.import_csv(
                    ImportType.SALES,
                    self._write_csv(temp_path / "sales.csv", self._sales_rows()),
                ),
                self.import_service.import_csv(
                    ImportType.INVENTORY,
                    self._write_csv(temp_path / "inventory.csv", self._inventory_rows()),
                ),
                self.import_service.import_csv(
                    ImportType.FULFILLMENT,
                    self._write_csv(temp_path / "fulfillment.csv", self._fulfillment_rows()),
                ),
            ]

        return SeedRunResult(import_results=results)

    def _write_csv(self, destination: Path, rows: list[dict[str, object]]) -> Path:
        if not rows:
            raise ValueError("Seed CSV rows cannot be empty")

        fieldnames = list(rows[0].keys())
        with destination.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return destination

    def _supplier_rows(self) -> list[dict[str, object]]:
        return [
            {
                "supplier_code": "SUP-IND-01",
                "name": "Banyan Components",
                "country_code": "IN",
                "region": "APAC",
                "lead_time_days": 18,
                "reliability_score": 92.5,
                "active": 1,
            },
            {
                "supplier_code": "SUP-VNM-01",
                "name": "Saigon Fulfillment Goods",
                "country_code": "VN",
                "region": "APAC",
                "lead_time_days": 22,
                "reliability_score": 88.0,
                "active": 1,
            },
            {
                "supplier_code": "SUP-USA-01",
                "name": "North Harbor Retail Supply",
                "country_code": "US",
                "region": "NA",
                "lead_time_days": 8,
                "reliability_score": 95.0,
                "active": 1,
            },
            {
                "supplier_code": "SUP-MEX-01",
                "name": "Nuevo Transit Works",
                "country_code": "MX",
                "region": "LATAM",
                "lead_time_days": 12,
                "reliability_score": 84.5,
                "active": 1,
            },
        ]

    def _product_rows(self) -> list[dict[str, object]]:
        return [
            {
                "sku": "CW-BAG-001",
                "name": "Transit Pack",
                "category": "Travel Gear",
                "brand": "ChainWatch Demo",
                "status": "active",
                "origin_country_code": "IN",
                "default_supplier_code": "SUP-IND-01",
                "alternate_supplier_codes": "SUP-VNM-01",
            },
            {
                "sku": "CW-LAMP-002",
                "name": "Warehouse Lamp",
                "category": "Lighting",
                "brand": "ChainWatch Demo",
                "status": "active",
                "origin_country_code": "VN",
                "default_supplier_code": "SUP-VNM-01",
                "alternate_supplier_codes": "SUP-IND-01|SUP-USA-01",
            },
            {
                "sku": "CW-DESK-003",
                "name": "Ops Desk Stand",
                "category": "Office",
                "brand": "ChainWatch Demo",
                "status": "active",
                "origin_country_code": "US",
                "default_supplier_code": "SUP-USA-01",
                "alternate_supplier_codes": "SUP-MEX-01",
            },
            {
                "sku": "CW-CASE-004",
                "name": "Field Case",
                "category": "Accessories",
                "brand": "ChainWatch Demo",
                "status": "active",
                "origin_country_code": "MX",
                "default_supplier_code": "SUP-MEX-01",
                "alternate_supplier_codes": "SUP-USA-01",
            },
        ]

    def _sales_rows(self) -> list[dict[str, object]]:
        base_units = {
            "CW-BAG-001": 48,
            "CW-LAMP-002": 34,
            "CW-DESK-003": 28,
            "CW-CASE-004": 42,
        }
        unit_price = {
            "CW-BAG-001": 79.0,
            "CW-LAMP-002": 64.0,
            "CW-DESK-003": 58.0,
            "CW-CASE-004": 49.0,
        }
        start_date = date(2023, 5, 6)
        rows: list[dict[str, object]] = []

        for week_number in range(156):
            sales_date = start_date + timedelta(days=7 * week_number)
            for sku, units in base_units.items():
                seasonal_multiplier = 1.0
                if sales_date.month in {11, 12}:
                    seasonal_multiplier += 0.35
                if sales_date.month in {6, 7} and sku in {"CW-BAG-001", "CW-CASE-004"}:
                    seasonal_multiplier += 0.20
                if sales_date.month in {1, 2} and sku == "CW-DESK-003":
                    seasonal_multiplier += 0.15

                promo_flag = 1 if week_number % 13 == 0 else 0
                stockout_flag = 1 if sku == "CW-LAMP-002" and week_number in {45, 46, 92} else 0
                if promo_flag:
                    seasonal_multiplier += 0.10
                if stockout_flag:
                    seasonal_multiplier -= 0.15

                week_units = max(8, int(round(units * seasonal_multiplier)))
                returns_qty = max(0, int(round(week_units * 0.04)))
                gross_revenue = round(week_units * unit_price[sku], 2)
                net_revenue = round(gross_revenue - (returns_qty * unit_price[sku] * 0.5), 2)

                rows.append(
                    {
                        "product_sku": sku,
                        "sales_date": sales_date.isoformat(),
                        "channel": "web" if week_number % 4 else "marketplace",
                        "region_code": "NA" if sku in {"CW-DESK-003", "CW-CASE-004"} else "APAC",
                        "units_sold": week_units,
                        "gross_revenue": gross_revenue,
                        "net_revenue": net_revenue,
                        "returns_qty": returns_qty,
                        "promo_flag": promo_flag,
                        "stockout_flag": stockout_flag,
                    }
                )

        return rows

    def _inventory_rows(self) -> list[dict[str, object]]:
        return [
            {
                "product_sku": "CW-BAG-001",
                "warehouse_code": "WH-BLR",
                "snapshot_date": "2026-05-01T08:00:00+00:00",
                "on_hand_qty": 420,
                "reserved_qty": 55,
                "inbound_qty": 140,
                "reorder_point": 180,
                "safety_stock": 120,
                "days_of_cover": 24.5,
            },
            {
                "product_sku": "CW-LAMP-002",
                "warehouse_code": "WH-SGN",
                "snapshot_date": "2026-05-01T08:00:00+00:00",
                "on_hand_qty": 130,
                "reserved_qty": 42,
                "inbound_qty": 60,
                "reorder_point": 150,
                "safety_stock": 90,
                "days_of_cover": 10.1,
            },
            {
                "product_sku": "CW-DESK-003",
                "warehouse_code": "WH-CHI",
                "snapshot_date": "2026-05-01T08:00:00+00:00",
                "on_hand_qty": 210,
                "reserved_qty": 28,
                "inbound_qty": 40,
                "reorder_point": 100,
                "safety_stock": 60,
                "days_of_cover": 18.2,
            },
            {
                "product_sku": "CW-CASE-004",
                "warehouse_code": "WH-MTY",
                "snapshot_date": "2026-05-01T08:00:00+00:00",
                "on_hand_qty": 96,
                "reserved_qty": 18,
                "inbound_qty": 120,
                "reorder_point": 110,
                "safety_stock": 70,
                "days_of_cover": 8.0,
            },
        ]

    def _fulfillment_rows(self) -> list[dict[str, object]]:
        return [
            {
                "product_sku": "CW-BAG-001",
                "region_code": "APAC",
                "warehouse_code": "WH-BLR",
                "captured_at": "2026-05-01T09:00:00+00:00",
                "backlog_orders": 18,
                "avg_ship_delay_hours": 6.5,
                "on_time_rate": 0.95,
                "sla_risk_level": 2,
            },
            {
                "product_sku": "CW-LAMP-002",
                "region_code": "APAC",
                "warehouse_code": "WH-SGN",
                "captured_at": "2026-05-01T09:00:00+00:00",
                "backlog_orders": 54,
                "avg_ship_delay_hours": 19.0,
                "on_time_rate": 0.84,
                "sla_risk_level": 4,
            },
            {
                "product_sku": "CW-DESK-003",
                "region_code": "NA",
                "warehouse_code": "WH-CHI",
                "captured_at": "2026-05-01T09:00:00+00:00",
                "backlog_orders": 22,
                "avg_ship_delay_hours": 8.0,
                "on_time_rate": 0.91,
                "sla_risk_level": 3,
            },
            {
                "product_sku": "CW-CASE-004",
                "region_code": "NA",
                "warehouse_code": "WH-MTY",
                "captured_at": "2026-05-01T09:00:00+00:00",
                "backlog_orders": 37,
                "avg_ship_delay_hours": 13.5,
                "on_time_rate": 0.88,
                "sla_risk_level": 3,
            },
        ]
