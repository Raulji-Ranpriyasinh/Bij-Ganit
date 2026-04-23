"""Item schemas (Sprint 2.6)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.tax import TaxInput, TaxOut


class ItemBase(BaseModel):
    name: str
    description: str | None = None
    price: int = 0
    tax_per_item: bool = False
    unit_id: int | None = None
    currency_id: int | None = None


class ItemCreate(ItemBase):
    taxes: list[TaxInput] = []


class ItemUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: int | None = None
    tax_per_item: bool | None = None
    unit_id: int | None = None
    currency_id: int | None = None
    taxes: list[TaxInput] | None = None


class ItemOut(ItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    company_id: int | None = None
    creator_id: int | None = None
    taxes: list[TaxOut] = []
    created_at: datetime
    updated_at: datetime


class ItemDeleteRequest(BaseModel):
    ids: list[int]
