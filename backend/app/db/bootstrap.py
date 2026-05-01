from __future__ import annotations

from pathlib import Path

from app.db.connection import SQLiteConnectionFactory

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def bootstrap_database(connection_factory: SQLiteConnectionFactory) -> None:
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    with connection_factory.transaction() as connection:
        connection.executescript(schema_sql)

