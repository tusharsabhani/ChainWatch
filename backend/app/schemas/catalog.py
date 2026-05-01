from __future__ import annotations

from pydantic import BaseModel


class SupplierCreate(BaseModel):
    supplier_code: str
    name: str
    country_code: str
    region: str | None = None
    lead_time_days: int | None = None
    reliability_score: float | None = None
    active: int = 1


class SupplierRecord(SupplierCreate):
    id: int
    created_at: str
    updated_at: str


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


class ProductSupplierLink(BaseModel):
    supplier_id: int
    is_primary: int
    supplier_sku: str | None = None
    lead_time_days: int | None = None
    min_order_qty: int | None = None
