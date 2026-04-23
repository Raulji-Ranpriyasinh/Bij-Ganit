"""Customer request / response schemas (Sprint 2.4)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.schemas.address import AddressInput, AddressOut


class CustomerBase(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    contact_name: str | None = None
    company_name: str | None = None
    website: str | None = None
    enable_portal: bool = False
    currency_id: int | None = None


class CustomerCreate(CustomerBase):
    password: str | None = None
    billing: AddressInput | None = None
    shipping: AddressInput | None = None


class CustomerUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    contact_name: str | None = None
    company_name: str | None = None
    website: str | None = None
    enable_portal: bool | None = None
    currency_id: int | None = None
    password: str | None = None
    billing: AddressInput | None = None
    shipping: AddressInput | None = None


class CustomerOut(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    billing: AddressOut | None = None
    shipping: AddressOut | None = None
    created_at: datetime
    updated_at: datetime


class CustomerDeleteRequest(BaseModel):
    ids: list[int]


class CustomerStats(BaseModel):
    customer_id: int
    total_customers: int
    # Invoice/estimate totals are placeholders until those tables land in a
    # later sprint — they're exposed now so the frontend contract is stable.
    total_invoices: int = 0
    total_estimates: int = 0
    total_payments: int = 0
    due_amount: int = 0
