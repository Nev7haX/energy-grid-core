"""Historical storage abstraction and in-memory implementation."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import timezone
from typing import Iterable

from sqlalchemy import select

from app.core.database import DatabaseManager
from app.models.telemetry_event import TelemetryEvent

from .connector_interfaces import TelemetrySample


@dataclass(slots=True)
class HistoryQuery:
    """History query parameters.

    Attributes:
        device_id: Unique device identifier.
        metric_name: Optional metric filter.
        limit: Maximum number of rows to return.
    """

    device_id: str
    metric_name: str | None = None
    limit: int = 200


class HistoryStoragePort(ABC):
    """Abstract interface for historical telemetry persistence."""

    @abstractmethod
    async def append_records(self, records: Iterable[TelemetrySample]) -> None:
        """Persist telemetry records.

        Args:
            records: Iterable of telemetry records.

        Returns:
            None.
        """

    @abstractmethod
    async def query_history(self, query: HistoryQuery) -> list[TelemetrySample]:
        """Query historical telemetry records.

        Args:
            query: History query parameters.

        Returns:
            Matching telemetry records in ascending time order.
        """

    @abstractmethod
    async def query_latest_snapshot(self, device_id: str) -> TelemetrySample | None:
        """Return the latest telemetry record for one device.

        Args:
            device_id: Unique device identifier.

        Returns:
            Latest telemetry record or None.
        """


class InMemoryHistoryStorage(HistoryStoragePort):
    """Bounded in-memory history storage useful for demos and tests."""

    def __init__(self, retention_per_device: int) -> None:
        """Initialize in-memory storage.

        Args:
            retention_per_device: Maximum retained rows per device.

        Returns:
            None.
        """
        self._retention_per_device = retention_per_device
        self._records: dict[str, deque[TelemetrySample]] = defaultdict(
            lambda: deque(maxlen=self._retention_per_device)
        )
        self._lock = asyncio.Lock()

    async def append_records(self, records: Iterable[TelemetrySample]) -> None:
        """Persist telemetry records in bounded device-specific buffers.

        Args:
            records: Iterable of telemetry records.

        Returns:
            None.
        """
        async with self._lock:
            for record in records:
                self._records[record.device_id].append(record)

    async def query_history(self, query: HistoryQuery) -> list[TelemetrySample]:
        """Return historical telemetry rows for a device.

        Args:
            query: History query parameters.

        Returns:
            Matching telemetry records in ascending time order.
        """
        async with self._lock:
            records = list(self._records.get(query.device_id, ()))
            if query.metric_name is not None:
                records = [record for record in records if record.metric_name == query.metric_name]
            return records[-query.limit :]

    async def query_latest_snapshot(self, device_id: str) -> TelemetrySample | None:
        """Return the latest telemetry row for one device.

        Args:
            device_id: Unique device identifier.

        Returns:
            Latest telemetry record or None.
        """
        async with self._lock:
            records = self._records.get(device_id)
            if not records:
                return None
            return records[-1]


class SQLAlchemyHistoryStorage(HistoryStoragePort):
    """SQLAlchemy-backed history storage for production-style persistence."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        """Initialize SQLAlchemy-backed storage.

        Args:
            database_manager: Shared database manager.

        Returns:
            None.
        """
        self._database_manager = database_manager

    async def append_records(self, records: Iterable[TelemetrySample]) -> None:
        """Persist telemetry records to the database.

        Args:
            records: Iterable of telemetry records.

        Returns:
            None.
        """
        record_list = list(records)
        if not record_list:
            return
        await asyncio.to_thread(self._append_records_sync, record_list)

    def _append_records_sync(self, records: list[TelemetrySample]) -> None:
        """Persist telemetry records using a blocking ORM session.

        Args:
            records: Telemetry records to persist.

        Returns:
            None.
        """
        with self._database_manager.get_session() as session:
            session.add_all(
                [
                    TelemetryEvent(
                        device_id=record.device_id,
                        metric_name=record.metric_name,
                        metric_value=record.metric_value,
                        quality=record.quality,
                        occurred_at=record.occurred_at,
                        attributes=dict(record.attributes),
                    )
                    for record in records
                ]
            )
            session.commit()

    async def query_history(self, query: HistoryQuery) -> list[TelemetrySample]:
        """Query historical telemetry records from the database.

        Args:
            query: History query parameters.

        Returns:
            Matching telemetry rows in ascending time order.
        """
        return await asyncio.to_thread(self._query_history_sync, query)

    def _query_history_sync(self, query: HistoryQuery) -> list[TelemetrySample]:
        """Run a blocking ORM query for telemetry history.

        Args:
            query: History query parameters.

        Returns:
            Matching telemetry rows.
        """
        statement = (
            select(TelemetryEvent)
            .where(TelemetryEvent.device_id == query.device_id)
            .order_by(TelemetryEvent.occurred_at.desc(), TelemetryEvent.id.desc())
            .limit(query.limit)
        )
        if query.metric_name is not None:
            statement = statement.where(TelemetryEvent.metric_name == query.metric_name)

        with self._database_manager.get_session() as session:
            rows = session.execute(statement).scalars().all()

        rows.reverse()
        return [self._to_sample(row) for row in rows]

    async def query_latest_snapshot(self, device_id: str) -> TelemetrySample | None:
        """Return the latest telemetry row for one device.

        Args:
            device_id: Unique device identifier.

        Returns:
            Latest telemetry sample or None.
        """
        return await asyncio.to_thread(self._query_latest_snapshot_sync, device_id)

    def _query_latest_snapshot_sync(self, device_id: str) -> TelemetrySample | None:
        """Run a blocking ORM query for the latest telemetry row.

        Args:
            device_id: Unique device identifier.

        Returns:
            Latest telemetry sample or None.
        """
        statement = (
            select(TelemetryEvent)
            .where(TelemetryEvent.device_id == device_id)
            .order_by(TelemetryEvent.occurred_at.desc(), TelemetryEvent.id.desc())
            .limit(1)
        )
        with self._database_manager.get_session() as session:
            row = session.execute(statement).scalar_one_or_none()
        return None if row is None else self._to_sample(row)

    @staticmethod
    def _to_sample(row: TelemetryEvent) -> TelemetrySample:
        """Convert an ORM telemetry row into the normalized domain model.

        Args:
            row: ORM telemetry row.

        Returns:
            Normalized telemetry sample.
        """
        occurred_at = row.occurred_at
        if occurred_at.tzinfo is None:
            occurred_at = occurred_at.replace(tzinfo=timezone.utc)
        return TelemetrySample(
            device_id=row.device_id,
            metric_name=row.metric_name,
            metric_value=row.metric_value,
            quality=row.quality,
            occurred_at=occurred_at,
            attributes=dict(row.attributes or {}),
        )
