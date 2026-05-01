from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from typing import Any

from app.db.connection import SQLiteConnectionFactory


class SQLiteRepository:
    def __init__(self, connection_factory: SQLiteConnectionFactory) -> None:
        self.connection_factory = connection_factory

    def fetch_one(
        self,
        query: str,
        params: Sequence[Any] = (),
    ) -> sqlite3.Row | None:
        with self.connection_factory.connection() as connection:
            cursor = connection.execute(query, tuple(params))
            return cursor.fetchone()

    def fetch_all(
        self,
        query: str,
        params: Sequence[Any] = (),
    ) -> list[sqlite3.Row]:
        with self.connection_factory.connection() as connection:
            cursor = connection.execute(query, tuple(params))
            return cursor.fetchall()

    def execute(
        self,
        query: str,
        params: Sequence[Any] = (),
    ) -> int:
        with self.connection_factory.transaction() as connection:
            cursor = connection.execute(query, tuple(params))
            return cursor.rowcount

    def execute_insert(
        self,
        query: str,
        params: Sequence[Any] = (),
    ) -> int:
        with self.connection_factory.transaction() as connection:
            cursor = connection.execute(query, tuple(params))
            return int(cursor.lastrowid)

