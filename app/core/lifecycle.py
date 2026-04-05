"""Application lifecycle and dependency container wiring."""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from fastapi import FastAPI

from app.core.database import DatabaseManager
from app.services.connection_pool import DeviceConnectionPool
from app.services.forecast_interface import ForecastProvider, NoopForecastProvider
from app.services.history_storage import (
    HistoryStoragePort,
    InMemoryHistoryStorage,
    SQLAlchemyHistoryStorage,
)
from app.services.monitoring_service import MonitoringService
from app.services.state_manager import DeviceStateManager
from app.services.stream_processor import RealtimeStreamProcessor

from .config import Settings


@dataclass(slots=True)
class ServiceContainer:
    """Container for application-wide service singletons.

    Attributes:
    settings: Runtime settings.
        database_manager: Shared database manager when persistence is enabled.
        connection_pool: Device connection registry.
        history_storage: Historical data storage.
        state_manager: Latest state manager.
        stream_processor: Realtime telemetry processor.
        forecast_provider: Forecast provider implementation.
        monitoring_service: Monitoring orchestration service.
    """

    settings: Settings
    database_manager: DatabaseManager | None
    connection_pool: DeviceConnectionPool
    history_storage: HistoryStoragePort
    state_manager: DeviceStateManager
    stream_processor: RealtimeStreamProcessor
    forecast_provider: ForecastProvider
    monitoring_service: MonitoringService


def build_service_container(settings: Settings) -> ServiceContainer:
    """Create application service singletons.

    Args:
        settings: Runtime settings.

    Returns:
        Wired service container.
    """
    connection_pool = DeviceConnectionPool(max_connections=settings.max_connections)
    database_manager: DatabaseManager | None = None
    history_storage: HistoryStoragePort
    if settings.history_storage_backend == "memory":
        history_storage = InMemoryHistoryStorage(
            retention_per_device=settings.telemetry_retention_per_device
        )
    else:
        database_manager = DatabaseManager.create(settings.database_url)
        database_manager.create_schema()
        history_storage = SQLAlchemyHistoryStorage(database_manager=database_manager)
    state_manager = DeviceStateManager()
    forecast_provider = NoopForecastProvider()
    stream_processor = RealtimeStreamProcessor(
        history_storage=history_storage,
        state_manager=state_manager,
        queue_maxsize=settings.queue_maxsize,
        batch_size=settings.stream_batch_size,
        flush_interval_seconds=settings.stream_flush_interval_seconds,
    )
    monitoring_service = MonitoringService(
        connection_pool=connection_pool,
        state_manager=state_manager,
        history_storage=history_storage,
        forecast_provider=forecast_provider,
    )
    return ServiceContainer(
        settings=settings,
        database_manager=database_manager,
        connection_pool=connection_pool,
        history_storage=history_storage,
        state_manager=state_manager,
        stream_processor=stream_processor,
        forecast_provider=forecast_provider,
        monitoring_service=monitoring_service,
    )


def create_lifespan(settings: Settings):
    """Create a FastAPI lifespan handler.

    Args:
        settings: Runtime settings.

    Returns:
        Async lifespan callable.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Initialize and tear down application resources.

        Args:
            app: FastAPI application instance.

        Returns:
            Async iterator controlling lifespan scope.
        """
        container = build_service_container(settings)
        app.state.container = container
        await container.stream_processor.start()
        try:
            yield
        finally:
            await container.stream_processor.stop()
            if container.database_manager is not None:
                container.database_manager.dispose()

    return lifespan
