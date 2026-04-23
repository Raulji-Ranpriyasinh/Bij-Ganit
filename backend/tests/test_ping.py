"""Smoke tests (Sprint 0.1)."""

from fastapi.testclient import TestClient

from app.main import app


def test_ping() -> None:
    client = TestClient(app)
    response = client.get("/api/ping")
    assert response.status_code == 200
    assert response.json() == {"success": "ok"}
