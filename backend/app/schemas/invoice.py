"""Schemas for Invoice creation and output (Sprint 3).
"""

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

from app.schemas.tax import TaxInput, TaxOut


class InvoiceItemInput(BaseModel):
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


class InvoiceCreate(BaseModel):
    customer_id: int | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    discount: int = 0
    discount_type: str | None = None
    items: list[InvoiceItemInput] = []
    taxes: list[TaxInput] = []


class InvoiceItemOut(BaseModel):
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


class InvoiceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    sub_total: int
    tax: int
    total: int
    due_amount: int
    items: list[InvoiceItemOut] = []
    created_at: datetime
    updated_at: datetime
