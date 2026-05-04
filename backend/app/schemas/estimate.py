"""Schemas for Estimates (Sprint 4).
"""

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

from app.schemas.tax import TaxInput, TaxOut


class EstimateItemInput(BaseModel):
    name: str
    description: str | None = None
    price: int = 0
    quantity: int = 1
    discount: int = 0
    discount_val: int = 0
    tax: int = 0
    unit_name: str | None = None
    item_id: int | None = None
    taxes: list[TaxInput] = []


class EstimateCreate(BaseModel):
    customer_id: int | None = None
    estimate_date: date | None = None
    expiry_date: date | None = None
    items: list[EstimateItemInput] = []
    taxes: list[TaxInput] = []


class EstimateItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    price: int
    quantity: int
    discount: int
    discount_val: int
    tax: int
    total: int
    created_at: datetime
    updated_at: datetime


class EstimateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estimate_number: str | None = None
    estimate_date: date | None = None
    expiry_date: date | None = None
    sub_total: int
    tax: int
    total: int
    items: list[EstimateItemOut] = []
    created_at: datetime
    updated_at: datetime
