from __future__ import annotations

import argparse
from pathlib import Path

from app.config import get_settings
from app.schemas.imports import ImportType
from app.services.imports.service import CSVImportService
from app.services.runtime import bootstrap_runtime


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a ChainWatch CSV file")
    parser.add_argument(
        "import_type",
        choices=[import_type.value for import_type in ImportType],
        help="Type of CSV data being imported",
    )
    parser.add_argument("source_path", help="Path to the CSV file")
    args = parser.parse_args()

    settings = get_settings()
    runtime = bootstrap_runtime(settings)
    import_service = CSVImportService(
        settings=settings,
        storage=runtime.storage,
        database=runtime.database,
    )
    result = import_service.import_csv(
        ImportType(args.import_type),
        Path(args.source_path),
    )

    print(
        f"{result.import_type.value}: {result.status.value} "
        f"(rows={result.row_count}, inserted={result.inserted_count}, errors={result.error_count})"
    )
    print(f"raw: {result.raw_path}")
    print(f"processed: {result.processed_summary_path}")
    if result.notes:
        print(result.notes)


if __name__ == "__main__":
    main()
