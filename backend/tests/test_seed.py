from __future__ import annotations

from app.db.repositories.system_repository import SystemRepository
from app.schemas.imports import ImportStatus
from app.services.imports.seed import DemoSeedService


def test_demo_seed_populates_local_database(runtime) -> None:
    seed_service = DemoSeedService(
        settings=runtime.settings,
        storage=runtime.storage,
        database=runtime.database,
    )

    result = seed_service.seed_demo_data()

    assert len(result.import_results) == 5
    assert all(import_result.status == ImportStatus.COMPLETED for import_result in result.import_results)

    system_repository = SystemRepository(runtime.database)
    assert system_repository.count_rows("suppliers") == 4
    assert system_repository.count_rows("products") == 4
    assert system_repository.count_rows("sales_history") == 624
    assert system_repository.count_rows("inventory_snapshots") == 4
    assert system_repository.count_rows("fulfillment_snapshots") == 4
    assert system_repository.count_rows("imports") == 5
