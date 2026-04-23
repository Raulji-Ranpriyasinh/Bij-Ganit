"""Company request / response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CompanyCreate(BaseModel):
    name: str
    slug: str | None = None


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    unique_hash: str | None = None
    owner_id: int | None = None
    created_at: datetime
    updated_at: datetime


class CompanyDeleteRequest(BaseModel):
    ids: list[int]
