"""Tests for the SQLAlchemy-backed history storage."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.core.database import DatabaseManager
from app.services.connector_interfaces import TelemetrySample
from app.services.history_storage import HistoryQuery, SQLAlchemyHistoryStorage


async def _seed_storage(storage: SQLAlchemyHistoryStorage) -> None:
    """Insert fixture telemetry into the storage backend.

    Args:
        storage: SQLAlchemy-backed storage instance.

    Returns:
        None.
    """
    base_time = datetime.now(timezone.utc)
    await storage.append_records(
        [
            TelemetrySample(
                device_id="meter-001",
                metric_name="power_kw",
                metric_value=10.5,
                occurred_at=base_time,
            ),
            TelemetrySample(
                device_id="meter-001",
                metric_name="power_kw",
                metric_value=11.0,
                occurred_at=base_time + timedelta(seconds=1),
            ),
            TelemetrySample(
                device_id="meter-001",
                metric_name="voltage_v",
                metric_value=220.0,
                occurred_at=base_time + timedelta(seconds=2),
            ),
        ]
    )


def test_sqlalchemy_history_storage_round_trip(tmp_path) -> None:
    """Ensure SQLAlchemy-backed history storage can persist and query telemetry.

    Args:
        tmp_path: Temporary directory fixture.

    Returns:
        None.
    """
    database_path = tmp_path / "history.db"
    database_manager = DatabaseManager.create(f"sqlite:///{database_path}")
    database_manager.create_schema()
    storage = SQLAlchemyHistoryStorage(database_manager)

    import asyncio

    asyncio.run(_seed_storage(storage))

    power_rows = asyncio.run(
        storage.query_history(
            HistoryQuery(device_id="meter-001", metric_name="power_kw", limit=10)
        )
    )
    assert len(power_rows) == 2
    assert [row.metric_value for row in power_rows] == [10.5, 11.0]

    latest_row = asyncio.run(storage.query_latest_snapshot("meter-001"))
    assert latest_row is not None
    assert latest_row.metric_name == "voltage_v"
    assert latest_row.metric_value == 220.0

    database_manager.dispose()
