from __future__ import annotations

from pydantic import BaseModel


class ProductCreate(BaseModel):
    sku: str
    name: str
    category: str
    brand: str | None = None
    status: str = "active"
    default_supplier_id: int | None = None
    origin_country_code: str | None = None


class ProductRecord(ProductCreate):
    id: int
    created_at: str
    updated_at: str

