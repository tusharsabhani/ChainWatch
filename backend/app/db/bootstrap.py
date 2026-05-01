from __future__ import annotations

from pathlib import Path
import sqlite3

from app.db.connection import SQLiteConnectionFactory

SCHEMA_PATH = Path(__file__).with_name("schema.sql")

REPORTS_TABLE_SQL = """
CREATE TABLE reports (
    id TEXT PRIMARY KEY,
    report_type TEXT NOT NULL,
    scope_type TEXT NOT NULL,
    scope_id TEXT,
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('queued', 'running', 'completed', 'partial', 'failed')),
    requested_by TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    json_path TEXT,
    markdown_path TEXT,
    summary TEXT,
    error_message TEXT
)
"""


def bootstrap_database(connection_factory: SQLiteConnectionFactory) -> None:
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with connection_factory.transaction() as connection:
        connection.executescript(schema_sql)
        _migrate_reports_table_for_partial_status(connection)
        connection.executescript(schema_sql)


def _migrate_reports_table_for_partial_status(connection: sqlite3.Connection) -> None:
    row = connection.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'reports'
        """
    ).fetchone()
    if row is None:
        return

    table_sql = str(row["sql"]).lower()
    if "'partial'" in table_sql:
        return

    connection.execute("ALTER TABLE reports RENAME TO reports_legacy")
    connection.execute(REPORTS_TABLE_SQL)
    connection.execute(
        """
        INSERT INTO reports (
            id,
            report_type,
            scope_type,
            scope_id,
            title,
            status,
            requested_by,
            created_at,
            completed_at,
            json_path,
            markdown_path,
            summary,
            error_message
        )
        SELECT
            id,
            report_type,
            scope_type,
            scope_id,
            title,
            status,
            requested_by,
            created_at,
            completed_at,
            json_path,
            markdown_path,
            summary,
            error_message
        FROM reports_legacy
        """
    )
    connection.execute("DROP TABLE reports_legacy")
