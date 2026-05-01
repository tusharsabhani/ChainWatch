from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import datetime, timezone

from app.db.repositories.base import SQLiteRepository
from app.schemas.catalog import (
    ProductCreate,
    ProductRecord,
    ProductSupplierLink,
    SupplierCreate,
    SupplierRecord,
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _placeholders(items: Sequence[object]) -> str:
    return ", ".join("?" for _ in items)


class CatalogRepository(SQLiteRepository):
    def get_product_by_id(
        self,
        product_id: int,
        connection: sqlite3.Connection | None = None,
    ) -> ProductRecord | None:
        row = self.fetch_one(
            """
            SELECT
                id,
                sku,
                name,
                category,
                brand,
                status,
                default_supplier_id,
                origin_country_code,
                created_at,
                updated_at
            FROM products
            WHERE id = ?
            """,
            (product_id,),
            connection=connection,
        )
        if row is None:
            return None
        return ProductRecord.model_validate(dict(row))

    def create_product(
        self,
        product: ProductCreate,
        connection: sqlite3.Connection | None = None,
    ) -> int:
        timestamp = _utc_now_iso()
        return self.execute_insert(
            """
            INSERT INTO products (
                sku,
                name,
                category,
                brand,
                status,
                default_supplier_id,
                origin_country_code,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product.sku,
                product.name,
                product.category,
                product.brand,
                product.status,
                product.default_supplier_id,
                product.origin_country_code,
                timestamp,
                timestamp,
            ),
            connection=connection,
        )

    def get_product_by_sku(
        self,
        sku: str,
        connection: sqlite3.Connection | None = None,
    ) -> ProductRecord | None:
        row = self.fetch_one(
            """
            SELECT
                id,
                sku,
                name,
                category,
                brand,
                status,
                default_supplier_id,
                origin_country_code,
                created_at,
                updated_at
            FROM products
            WHERE sku = ?
            """,
            (sku,),
            connection=connection,
        )
        if row is None:
            return None
        return ProductRecord.model_validate(dict(row))

    def get_supplier_by_code(
        self,
        supplier_code: str,
        connection: sqlite3.Connection | None = None,
    ) -> SupplierRecord | None:
        row = self.fetch_one(
            """
            SELECT
                id,
                supplier_code,
                name,
                country_code,
                region,
                lead_time_days,
                reliability_score,
                active,
                created_at,
                updated_at
            FROM suppliers
            WHERE supplier_code = ?
            """,
            (supplier_code,),
            connection=connection,
        )
        if row is None:
            return None
        return SupplierRecord.model_validate(dict(row))

    def upsert_supplier(
        self,
        supplier: SupplierCreate,
        connection: sqlite3.Connection | None = None,
    ) -> int:
        timestamp = _utc_now_iso()
        self.execute(
            """
            INSERT INTO suppliers (
                supplier_code,
                name,
                country_code,
                region,
                lead_time_days,
                reliability_score,
                active,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(supplier_code) DO UPDATE SET
                name = excluded.name,
                country_code = excluded.country_code,
                region = excluded.region,
                lead_time_days = excluded.lead_time_days,
                reliability_score = excluded.reliability_score,
                active = excluded.active,
                updated_at = excluded.updated_at
            """,
            (
                supplier.supplier_code,
                supplier.name,
                supplier.country_code,
                supplier.region,
                supplier.lead_time_days,
                supplier.reliability_score,
                supplier.active,
                timestamp,
                timestamp,
            ),
            connection=connection,
        )
        persisted_supplier = self.get_supplier_by_code(
            supplier.supplier_code,
            connection=connection,
        )
        if persisted_supplier is None:
            raise RuntimeError(f"Supplier upsert failed for {supplier.supplier_code}")
        return persisted_supplier.id

    def upsert_product(
        self,
        product: ProductCreate,
        connection: sqlite3.Connection | None = None,
    ) -> int:
        timestamp = _utc_now_iso()
        self.execute(
            """
            INSERT INTO products (
                sku,
                name,
                category,
                brand,
                status,
                default_supplier_id,
                origin_country_code,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sku) DO UPDATE SET
                name = excluded.name,
                category = excluded.category,
                brand = excluded.brand,
                status = excluded.status,
                default_supplier_id = excluded.default_supplier_id,
                origin_country_code = excluded.origin_country_code,
                updated_at = excluded.updated_at
            """,
            (
                product.sku,
                product.name,
                product.category,
                product.brand,
                product.status,
                product.default_supplier_id,
                product.origin_country_code,
                timestamp,
                timestamp,
            ),
            connection=connection,
        )
        persisted_product = self.get_product_by_sku(product.sku, connection=connection)
        if persisted_product is None:
            raise RuntimeError(f"Product upsert failed for {product.sku}")
        return persisted_product.id

    def replace_product_suppliers(
        self,
        product_id: int,
        supplier_links: list[ProductSupplierLink],
        connection: sqlite3.Connection | None = None,
    ) -> None:
        timestamp = _utc_now_iso()
        self.execute(
            "DELETE FROM product_suppliers WHERE product_id = ?",
            (product_id,),
            connection=connection,
        )
        for link in supplier_links:
            self.execute(
                """
                INSERT INTO product_suppliers (
                    product_id,
                    supplier_id,
                    is_primary,
                    supplier_sku,
                    lead_time_days,
                    min_order_qty,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    product_id,
                    link.supplier_id,
                    link.is_primary,
                    link.supplier_sku,
                    link.lead_time_days,
                    link.min_order_qty,
                    timestamp,
                    timestamp,
                ),
                connection=connection,
            )

    def list_product_supplier_ids(
        self,
        product_id: int,
        connection: sqlite3.Connection | None = None,
    ) -> list[int]:
        rows = self.fetch_all(
            """
            SELECT supplier_id
            FROM product_suppliers
            WHERE product_id = ?
            ORDER BY is_primary DESC, supplier_id ASC
            """,
            (product_id,),
            connection=connection,
        )
        return [int(row["supplier_id"]) for row in rows]

    def list_products_by_ids(self, product_ids: list[int]) -> list[ProductRecord]:
        if not product_ids:
            return []
        rows = self.fetch_all(
            f"""
            SELECT
                id,
                sku,
                name,
                category,
                brand,
                status,
                default_supplier_id,
                origin_country_code,
                created_at,
                updated_at
            FROM products
            WHERE id IN ({_placeholders(product_ids)})
            ORDER BY id ASC
            """,
            product_ids,
        )
        return [ProductRecord.model_validate(dict(row)) for row in rows]

    def list_all_products(self, *, active_only: bool = True) -> list[ProductRecord]:
        where_clause = "WHERE status = 'active'" if active_only else ""
        rows = self.fetch_all(
            f"""
            SELECT
                id,
                sku,
                name,
                category,
                brand,
                status,
                default_supplier_id,
                origin_country_code,
                created_at,
                updated_at
            FROM products
            {where_clause}
            ORDER BY name ASC
            """
        )
        return [ProductRecord.model_validate(dict(row)) for row in rows]

    def search_products(
        self,
        *,
        query: str | None = None,
        category: str | None = None,
        limit: int = 25,
    ) -> list[ProductRecord]:
        conditions: list[str] = []
        params: list[object] = []

        if query:
            conditions.append("(LOWER(name) LIKE ? OR LOWER(sku) LIKE ?)")
            query_value = f"%{query.strip().lower()}%"
            params.extend([query_value, query_value])
        if category:
            conditions.append("LOWER(category) = ?")
            params.append(category.strip().lower())

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = self.fetch_all(
            f"""
            SELECT
                id,
                sku,
                name,
                category,
                brand,
                status,
                default_supplier_id,
                origin_country_code,
                created_at,
                updated_at
            FROM products
            {where_clause}
            ORDER BY name ASC
            LIMIT ?
            """,
            [*params, limit],
        )
        return [ProductRecord.model_validate(dict(row)) for row in rows]

    def list_suppliers_by_country_codes(self, country_codes: list[str]) -> list[SupplierRecord]:
        if not country_codes:
            return []
        rows = self.fetch_all(
            f"""
            SELECT
                id,
                supplier_code,
                name,
                country_code,
                region,
                lead_time_days,
                reliability_score,
                active,
                created_at,
                updated_at
            FROM suppliers
            WHERE country_code IN ({_placeholders(country_codes)})
            ORDER BY name ASC
            """,
            country_codes,
        )
        return [SupplierRecord.model_validate(dict(row)) for row in rows]

    def list_products_by_supplier_countries(self, country_codes: list[str]) -> list[ProductRecord]:
        if not country_codes:
            return []
        rows = self.fetch_all(
            f"""
            SELECT DISTINCT
                p.id,
                p.sku,
                p.name,
                p.category,
                p.brand,
                p.status,
                p.default_supplier_id,
                p.origin_country_code,
                p.created_at,
                p.updated_at
            FROM products AS p
            INNER JOIN product_suppliers AS ps
                ON ps.product_id = p.id
            INNER JOIN suppliers AS s
                ON s.id = ps.supplier_id
            WHERE s.country_code IN ({_placeholders(country_codes)})
            ORDER BY p.name ASC
            """,
            country_codes,
        )
        return [ProductRecord.model_validate(dict(row)) for row in rows]

    def get_supplier_by_id(
        self,
        supplier_id: int,
        connection: sqlite3.Connection | None = None,
    ) -> SupplierRecord | None:
        row = self.fetch_one(
            """
            SELECT
                id,
                supplier_code,
                name,
                country_code,
                region,
                lead_time_days,
                reliability_score,
                active,
                created_at,
                updated_at
            FROM suppliers
            WHERE id = ?
            """,
            (supplier_id,),
            connection=connection,
        )
        if row is None:
            return None
        return SupplierRecord.model_validate(dict(row))

    def list_product_suppliers(self, product_id: int) -> list[SupplierRecord]:
        rows = self.fetch_all(
            """
            SELECT
                s.id,
                s.supplier_code,
                s.name,
                s.country_code,
                s.region,
                s.lead_time_days,
                s.reliability_score,
                s.active,
                s.created_at,
                s.updated_at
            FROM suppliers AS s
            INNER JOIN product_suppliers AS ps
                ON ps.supplier_id = s.id
            WHERE ps.product_id = ?
            ORDER BY ps.is_primary DESC, s.name ASC
            """,
            (product_id,),
        )
        return [SupplierRecord.model_validate(dict(row)) for row in rows]

    def list_all_product_ids(self, *, active_only: bool = True) -> list[int]:
        where_clause = "WHERE status = 'active'" if active_only else ""
        rows = self.fetch_all(
            f"""
            SELECT id
            FROM products
            {where_clause}
            ORDER BY id ASC
            """
        )
        return [int(row["id"]) for row in rows]

    def list_all_supplier_country_codes(self) -> list[str]:
        rows = self.fetch_all(
            """
            SELECT DISTINCT country_code
            FROM suppliers
            WHERE country_code IS NOT NULL
              AND country_code != ''
            ORDER BY country_code ASC
            """
        )
        return [str(row["country_code"]) for row in rows]

    def list_supplier_country_codes_for_product_ids(self, product_ids: list[int]) -> list[str]:
        if not product_ids:
            return []
        rows = self.fetch_all(
            f"""
            SELECT DISTINCT s.country_code
            FROM suppliers AS s
            INNER JOIN product_suppliers AS ps
                ON ps.supplier_id = s.id
            WHERE ps.product_id IN ({_placeholders(product_ids)})
              AND s.country_code IS NOT NULL
              AND s.country_code != ''
            ORDER BY s.country_code ASC
            """,
            product_ids,
        )
        return [str(row["country_code"]) for row in rows]
