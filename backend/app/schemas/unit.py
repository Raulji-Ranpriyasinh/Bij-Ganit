"""Unit schemas (Sprint 2.6)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UnitCreate(BaseModel):
    name: str


class UnitUpdate(BaseModel):
    name: str | None = None


class UnitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    company_id: int | None = None
    created_at: datetime
    updated_at: datetime
