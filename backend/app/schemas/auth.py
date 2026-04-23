"""Request / response schemas for the auth endpoints."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    type: str = "Bearer"
    token: str


class LogoutResponse(BaseModel):
    success: bool = True


class AuthCheckResponse(BaseModel):
    authenticated: bool
    user_id: int | None = None
