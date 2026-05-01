from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.main import create_app
from app.services.imports.seed import DemoSeedService
from app.services.runtime import bootstrap_runtime


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    return Settings(repo_root=tmp_path)


@pytest.fixture()
def app(settings: Settings):
    return create_app(settings)


@pytest.fixture()
def runtime(settings: Settings):
    return bootstrap_runtime(settings)


@pytest.fixture()
def seeded_runtime(runtime):
    seed_service = DemoSeedService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
    )
    seed_service.seed_demo_data()
    return runtime
