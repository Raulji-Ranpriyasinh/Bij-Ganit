"""TaxType + Tax schemas (Sprint 2.7, 2.8)."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TaxTypeCreate(BaseModel):
    name: str
    percent: Decimal = Decimal("0")
    compound_tax: bool = False
    collective_tax: bool = False
    type: str | None = None
    description: str | None = None


class TaxTypeUpdate(BaseModel):
    name: str | None = None
    percent: Decimal | None = None
    compound_tax: bool | None = None
    collective_tax: bool | None = None
    type: str | None = None
    description: str | None = None


class TaxTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    percent: Decimal
    compound_tax: bool
    collective_tax: bool
    type: str | None = None
    description: str | None = None
    company_id: int | None = None
    created_at: datetime
    updated_at: datetime


class TaxTypeDeleteRequest(BaseModel):
    ids: list[int]


# ---------------------------------------------------------------------------
# Per-line taxes (used inside Item payloads)


class TaxInput(BaseModel):
    tax_type_id: int
    amount: int = 0
    percent: Decimal = Decimal("0")
    compound_tax: bool = False


class TaxOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    amount: int
    percent: Decimal
    compound_tax: bool
    tax_type_id: int | None = None
