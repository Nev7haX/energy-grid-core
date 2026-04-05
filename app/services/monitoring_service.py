"""Monitoring-centric orchestration services."""

from __future__ import annotations

from app.core.exceptions import ValidationError

from .connection_pool import DeviceConnectionPool
from .forecast_interface import ForecastProvider, ForecastRequest
from .history_storage import HistoryQuery, HistoryStoragePort
from .state_manager import DeviceStateManager


class MonitoringService:
    """Compose pool, stream, history, and forecast capabilities for APIs."""

    def __init__(
        self,
        *,
        connection_pool: DeviceConnectionPool,
        state_manager: DeviceStateManager,
        history_storage: HistoryStoragePort,
        forecast_provider: ForecastProvider,
    ) -> None:
        """Initialize the monitoring service.

        Args:
            connection_pool: Active device connection pool.
            state_manager: Latest state manager.
            history_storage: Historical storage implementation.
            forecast_provider: Forecast provider implementation.

        Returns:
            None.
        """
        self._connection_pool = connection_pool
        self._state_manager = state_manager
        self._history_storage = history_storage
        self._forecast_provider = forecast_provider

    async def build_overview(self) -> dict[str, object]:
        """Build a monitoring overview optimized for dashboard reads.

        Args:
            None.

        Returns:
            Dashboard-ready monitoring overview.
        """
        pool_snapshot = await self._connection_pool.snapshot()
        states = await self._state_manager.list_states()

        healthy = sum(1 for state in states if state.health_state == "healthy")
        degraded = sum(1 for state in states if state.health_state == "degraded")

        return {
            "pool": pool_snapshot,
            "summary": {
                "tracked_devices": len(states),
                "healthy_devices": healthy,
                "degraded_devices": degraded,
            },
            "devices": [
                {
                    "device_id": state.device_id,
                    "health_state": state.health_state,
                    "quality": state.quality,
                    "last_seen_at": state.last_seen_at.isoformat(),
                    "latest_metrics": dict(state.latest_metrics),
                }
                for state in states
            ],
        }

    async def get_history(self, device_id: str, *, metric_name: str | None, limit: int) -> list[dict[str, object]]:
        """Return normalized device history rows.

        Args:
            device_id: Unique device identifier.
            metric_name: Optional metric filter.
            limit: Maximum number of rows to return.

        Returns:
            Serialized history rows.
        """
        rows = await self._history_storage.query_history(
            HistoryQuery(device_id=device_id, metric_name=metric_name, limit=limit)
        )
        return [
            {
                "device_id": row.device_id,
                "metric_name": row.metric_name,
                "metric_value": row.metric_value,
                "quality": row.quality,
                "occurred_at": row.occurred_at.isoformat(),
                "attributes": dict(row.attributes),
            }
            for row in rows
        ]

    async def forecast_device(self, device_id: str, *, metric_name: str, horizon: int) -> dict[str, object]:
        """Invoke the configured forecast provider for one device metric.

        Args:
            device_id: Unique device identifier.
            metric_name: Metric name to forecast.
            horizon: Number of future points.

        Returns:
            Serialized forecast payload.

        Raises:
            ValidationError: If no historical data exists.
        """
        history = await self._history_storage.query_history(
            HistoryQuery(device_id=device_id, metric_name=metric_name, limit=max(horizon * 5, horizon))
        )
        if not history:
            raise ValidationError(
                f"No historical records found for device '{device_id}' and metric '{metric_name}'."
            )

        result = await self._forecast_provider.forecast(
            ForecastRequest(
                device_id=device_id,
                history=history,
                horizon=horizon,
                metric_name=metric_name,
            )
        )
        return {
            "device_id": device_id,
            "metric_name": metric_name,
            "model_name": result.model_name,
            "points": [
                {
                    "timestamp": point.timestamp,
                    "predicted_value": point.predicted_value,
                    "confidence_low": point.confidence_low,
                    "confidence_high": point.confidence_high,
                }
                for point in result.points
            ],
            "metadata": dict(result.metadata),
        }

