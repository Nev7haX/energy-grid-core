"""Integration tests for the core runtime skeleton."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import get_settings
from main import create_app


def test_connect_ingest_and_query_overview(monkeypatch, tmp_path) -> None:
    """Ensure the core runtime can connect devices and expose monitoring data.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary directory fixture.

    Returns:
        None.
    """
    database_path = tmp_path / "integration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    monkeypatch.setenv("HISTORY_STORAGE_BACKEND", "sqlalchemy")
    get_settings.cache_clear()
    app = create_app()

    with TestClient(app) as client:
        connect_response = client.post(
            "/api/v1/devices/connect",
            json={
                "device_id": "meter-001",
                "protocol": "mock",
                "metadata": {"zone": "A1"},
            },
        )
        assert connect_response.status_code == 201

        ingest_response = client.post(
            "/api/v1/monitoring/ingest",
            json={
                "device_id": "meter-001",
                "metric_name": "power_kw",
                "metric_value": 12.5,
                "quality": "good",
            },
        )
        assert ingest_response.status_code == 202

        history_response = client.get("/api/v1/history/meter-001")
        assert history_response.status_code == 200
        assert history_response.json()["total"] >= 1

        overview_response = client.get("/api/v1/monitoring/overview")
        assert overview_response.status_code == 200
        assert overview_response.json()["data"]["summary"]["tracked_devices"] >= 1

    get_settings.cache_clear()

