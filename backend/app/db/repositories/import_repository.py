from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from app.db.repositories.base import SQLiteRepository
from app.schemas.imports import ImportStatus, ImportType


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ImportRepository(SQLiteRepository):
    def create_import_run(
        self,
        *,
        import_id: str,
        import_type: ImportType,
        filename: str,
        status: ImportStatus = ImportStatus.PROCESSING,
        connection: sqlite3.Connection | None = None,
    ) -> str:
        started_at = _utc_now_iso()
        self.execute(
            """
            INSERT INTO imports (
                id,
                import_type,
                filename,
                status,
                row_count,
                inserted_count,
                error_count,
                started_at,
                completed_at,
                notes
            )
            VALUES (?, ?, ?, ?, 0, 0, 0, ?, NULL, NULL)
            """,
            (import_id, import_type.value, filename, status.value, started_at),
            connection=connection,
        )
        return started_at

    def finalize_import_run(
        self,
        *,
        import_id: str,
        status: ImportStatus,
        row_count: int,
        inserted_count: int,
        error_count: int,
        notes: str | None,
        connection: sqlite3.Connection | None = None,
    ) -> str:
        completed_at = _utc_now_iso()
        self.execute(
            """
            UPDATE imports
            SET status = ?,
                row_count = ?,
                inserted_count = ?,
                error_count = ?,
                completed_at = ?,
                notes = ?
            WHERE id = ?
            """,
            (
                status.value,
                row_count,
                inserted_count,
                error_count,
                completed_at,
                notes,
                import_id,
            ),
            connection=connection,
        )
        return completed_at

    def get_import_run_row(
        self,
        import_id: str,
        connection: sqlite3.Connection | None = None,
    ) -> sqlite3.Row | None:
        return self.fetch_one(
            """
            SELECT
                id,
                import_type,
                filename,
                status,
                row_count,
                inserted_count,
                error_count,
                started_at,
                completed_at,
                notes
            FROM imports
            WHERE id = ?
            """,
            (import_id,),
            connection=connection,
        )

    def list_import_runs(self, connection: sqlite3.Connection | None = None) -> list[sqlite3.Row]:
        return self.fetch_all(
            """
            SELECT
                id,
                import_type,
                filename,
                status,
                row_count,
                inserted_count,
                error_count,
                started_at,
                completed_at,
                notes
            FROM imports
            ORDER BY started_at DESC
            """,
            connection=connection,
        )
