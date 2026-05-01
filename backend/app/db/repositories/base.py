from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from typing import Any

from app.db.connection import SQLiteConnectionFactory


class SQLiteRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def _connection_context(
        self,
        connection: sqlite3.Connection | None = None,
    ):
        if connection is not None:
            return _ExistingConnectionContext(connection)
        return self.connection_factory.connection()

    def fetch_one(
        self,
        query: str,
        params: Sequence[Any] = (),
        connection: sqlite3.Connection | None = None,
    ) -> sqlite3.Row | None:
        with self._connection_context(connection) as active_connection:
            cursor = active_connection.execute(query, tuple(params))
            return cursor.fetchone()

    def fetch_all(
        self,
        query: str,
        params: Sequence[Any] = (),
        connection: sqlite3.Connection | None = None,
    ) -> list[sqlite3.Row]:
        with self._connection_context(connection) as active_connection:
            cursor = active_connection.execute(query, tuple(params))
            return cursor.fetchall()

    def execute(
        self,
        query: str,
        params: Sequence[Any] = (),
        connection: sqlite3.Connection | None = None,
    ) -> int:
        if connection is not None:
            cursor = connection.execute(query, tuple(params))
            return cursor.rowcount
        with self.connection_factory.transaction() as active_connection:
            cursor = active_connection.execute(query, tuple(params))
            return cursor.rowcount

    def execute_insert(
        self,
        query: str,
        params: Sequence[Any] = (),
        connection: sqlite3.Connection | None = None,
    ) -> int:
        if connection is not None:
            cursor = connection.execute(query, tuple(params))
            return int(cursor.lastrowid)
        with self.connection_factory.transaction() as active_connection:
            cursor = active_connection.execute(query, tuple(params))
            return int(cursor.lastrowid)


class _ExistingConnectionContext:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def __enter__(self) -> sqlite3.Connection:
        return self.connection

    def __exit__(self, exc_type, exc, exc_tb) -> bool:
        return False
