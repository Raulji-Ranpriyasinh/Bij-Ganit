"""Address request / response schemas (Sprint 2.3)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

AddressType = Literal["billing", "shipping"]


class AddressInput(BaseModel):
    """Nested address payload inside Customer create/update."""

    name: str | None = None
    address_street_1: str | None = None
    address_street_2: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    phone: str | None = None
    fax: str | None = None
    country_id: int | None = None


class AddressOut(AddressInput):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: AddressType | None = None
    created_at: datetime
    updated_at: datetime
