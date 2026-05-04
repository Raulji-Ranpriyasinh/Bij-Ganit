"""Schemas for Payments (Sprint 4).
"""

from datetime import date, datetime
from pydantic import BaseModel, ConfigDict


class PaymentCreate(BaseModel):
    invoice_id: int | None = None
    amount: int
    payment_date: date | None = None
    notes: str | None = None
    payment_method_id: int | None = None


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    payment_number: str | None = None
    payment_date: date | None = None
    amount: int
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
