"""User request / response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    name: str
    email: EmailStr | None = None
    phone: str | None = None
    role: str = "user"


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    role: str | None = None
    password: str | None = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class UserDeleteRequest(BaseModel):
    ids: list[int]
