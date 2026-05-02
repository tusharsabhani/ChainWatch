from __future__ import annotations

from app.config import get_settings
from app.services.manual_external_risk_snapshot import persist_manual_external_risk_snapshot
from app.services.runtime import bootstrap_runtime


def main() -> None:
    settings = get_settings()
    runtime = bootstrap_runtime(settings)
    result = persist_manual_external_risk_snapshot(
        settings=settings,
        storage=runtime.storage,
        database=runtime.database,
    )

    print(
        "manual external risk snapshot stored "
        f"(events={result.event_count}, scores={result.score_count}, countries={','.join(result.country_codes)})"
    )
    for path in result.cache_paths:
        print(path)


if __name__ == "__main__":
    main()
