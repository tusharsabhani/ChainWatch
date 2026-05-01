from __future__ import annotations

from app.config import get_settings
from app.services.imports.seed import DemoSeedService
from app.services.runtime import bootstrap_runtime


def main() -> None:
    settings = get_settings()
    runtime = bootstrap_runtime(settings)
    seed_service = DemoSeedService(
        settings=settings,
        storage=runtime.storage,
        database=runtime.database,
    )
    result = seed_service.seed_demo_data()

    for import_result in result.import_results:
        print(
            f"{import_result.import_type.value}: {import_result.status.value} "
            f"(rows={import_result.row_count}, inserted={import_result.inserted_count}, errors={import_result.error_count})"
        )


if __name__ == "__main__":
    main()
