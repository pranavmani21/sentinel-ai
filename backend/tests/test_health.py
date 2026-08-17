"""Tests for operational endpoints."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from sentinel_api.main import app


def test_health_returns_service_metadata() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "SentinelAI API",
        "environment": "development",
    }


def test_readiness_returns_ok_when_database_is_available() -> None:
    with patch(
        "sentinel_api.main.database_is_ready",
        new=AsyncMock(return_value=True),
    ):
        with TestClient(app) as client:
            response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "SentinelAI API",
        "environment": "development",
    }


def test_readiness_returns_service_unavailable_when_database_is_unavailable() -> None:
    with patch(
        "sentinel_api.main.database_is_ready",
        new=AsyncMock(return_value=False),
    ):
        with TestClient(app) as client:
            response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "service": "SentinelAI API",
        "environment": "development",
    }
