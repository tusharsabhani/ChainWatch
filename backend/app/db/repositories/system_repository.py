from __future__ import annotations

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

