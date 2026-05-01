from __future__ import annotations

from datetime import datetime, timezone

from app.db.repositories.base import SQLiteRepository
from app.schemas.catalog import ProductCreate, ProductRecord


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class CatalogRepository(SQLiteRepository):
    def create_product(self, product: ProductCreate) -> int:
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
        )

    def get_product_by_sku(self, sku: str) -> ProductRecord | None:
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
        )
        if row is None:
            return None
        return ProductRecord.model_validate(dict(row))

