from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.db.bootstrap import bootstrap_database
from app.db.connection import SQLiteConnectionFactory
from app.services.storage import StorageManager


@dataclass(slots=True)
class RuntimeServices:
    settings: Settings
    storage: StorageManager
    database: SQLiteConnectionFactory


def bootstrap_runtime(settings: Settings) -> RuntimeServices:
    storage = StorageManager(settings)
    storage.ensure_runtime_paths()

    connection_factory = SQLiteConnectionFactory(
        settings.database_path,
        timeout_seconds=settings.sqlite_timeout_seconds,
    )
    bootstrap_database(connection_factory)

    return RuntimeServices(
        settings=settings,
        storage=storage,
        database=connection_factory,
    )

