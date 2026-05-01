from __future__ import annotations

import sqlite3

from app.db.repositories.base import SQLiteRepository


class SystemRepository(SQLiteRepository):
    def ping(self) -> bool:
        row = self.fetch_one("SELECT 1 AS ok")
        return row is not None and row["ok"] == 1

    def list_tables(self) -> list[str]:
        rows = self.fetch_all(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        )
        return [str(row["name"]) for row in rows]

    def count_rows(
        self,
        table_name: str,
        connection: sqlite3.Connection | None = None,
    ) -> int:
        allowed_tables = {
            "products",
            "suppliers",
            "product_suppliers",
            "sales_history",
            "inventory_snapshots",
            "fulfillment_snapshots",
            "imports",
        }
        if table_name not in allowed_tables:
            raise ValueError(f"Unsupported table count target: {table_name}")

        row = self.fetch_one(
            f"SELECT COUNT(*) AS row_count FROM {table_name}",
            connection=connection,
        )
        return int(row["row_count"]) if row is not None else 0
