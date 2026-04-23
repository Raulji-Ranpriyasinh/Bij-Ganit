"""Tests for the static lookup endpoints (Sprint 2.11).

These endpoints return bundled seed data with no DB access so we can run
them against the FastAPI TestClient directly.
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_countries_endpoint() -> None:
    r = client.get("/api/v1/countries")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 200
    assert {"id", "code", "name", "phonecode"} <= set(data[0].keys())


def test_currencies_endpoint() -> None:
    r = client.get("/api/v1/currencies")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 150
    codes = {c["code"] for c in data}
    assert {"USD", "EUR", "INR"} <= codes


def test_timezones_endpoint() -> None:
    r = client.get("/api/v1/timezones")
    assert r.status_code == 200
    data = r.json()
    assert data and {"key", "label"} <= set(data[0].keys())


def test_date_formats_endpoint() -> None:
    r = client.get("/api/v1/date/formats")
    assert r.status_code == 200
    data = r.json()
    assert data and {"carbon_format", "moment_format", "display"} <= set(data[0].keys())
