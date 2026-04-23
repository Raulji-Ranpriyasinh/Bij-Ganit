"""Unit tests for the security helpers (Sprint 1.5)."""

from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
    verify_token,
)


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("hunter2")
    assert hashed != "hunter2"
    assert verify_password("hunter2", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_jwt_roundtrip() -> None:
    token = create_access_token(subject=42)
    claims = verify_token(token)
    assert claims is not None
    assert claims["sub"] == "42"


def test_jwt_invalid_returns_none() -> None:
    assert verify_token("not-a-token") is None
