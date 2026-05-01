from __future__ import annotations

from app.db.repositories.catalog_repository import CatalogRepository
from app.db.repositories.system_repository import SystemRepository
from app.schemas.catalog import ProductCreate
from app.services.runtime import bootstrap_runtime


def test_bootstrap_creates_runtime_layout(settings) -> None:
    runtime = bootstrap_runtime(settings)

    expected_directories = (
        settings.data_dir,
        settings.imports_raw_dir,
        settings.imports_processed_dir,
        settings.reports_json_dir,
        settings.reports_markdown_dir,
        settings.cache_external_risk_dir,
        settings.logs_app_dir,
        settings.logs_agent_runs_dir,
    )

    for directory in expected_directories:
        assert directory.exists()
        assert directory.is_dir()

    assert settings.database_path.exists()
    assert runtime.database.database_path == settings.database_path


def test_bootstrap_creates_all_documented_tables(settings) -> None:
    runtime = bootstrap_runtime(settings)
    repository = SystemRepository(runtime.database)

    expected_tables = {
        "agent_runs",
        "chat_messages",
        "chat_sessions",
        "country_risk_scores",
        "fulfillment_snapshots",
        "imports",
        "inventory_snapshots",
        "product_suppliers",
        "products",
        "reports",
        "risk_events",
        "sales_history",
        "suppliers",
    }

    assert set(repository.list_tables()) == expected_tables


def test_bootstrap_is_idempotent(settings) -> None:
    first_runtime = bootstrap_runtime(settings)
    catalog_repository = CatalogRepository(first_runtime.database)
    product_id = catalog_repository.create_product(
        ProductCreate(
            sku="SKU-001",
            name="Starter Product",
            category="Accessories",
        )
    )

    second_runtime = bootstrap_runtime(settings)
    second_catalog_repository = CatalogRepository(second_runtime.database)
    persisted_product = second_catalog_repository.get_product_by_sku("SKU-001")

    assert persisted_product is not None
    assert persisted_product.id == product_id

