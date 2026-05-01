from __future__ import annotations

from app.db.repositories.catalog_repository import CatalogRepository
from app.schemas.catalog import ProductCreate
from app.services.runtime import bootstrap_runtime


def test_catalog_repository_can_write_and_read_products(settings) -> None:
    runtime = bootstrap_runtime(settings)
    repository = CatalogRepository(runtime.database)

    created_id = repository.create_product(
        ProductCreate(
            sku="SKU-100",
            name="Warehouse Lamp",
            category="Lighting",
            brand="ChainWatch Demo",
            origin_country_code="IN",
        )
    )

    stored_product = repository.get_product_by_sku("SKU-100")

    assert stored_product is not None
    assert stored_product.id == created_id
    assert stored_product.name == "Warehouse Lamp"
    assert stored_product.brand == "ChainWatch Demo"

