"""Forecast interface definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from .connector_interfaces import TelemetrySample


@dataclass(slots=True)
class ForecastRequest:
    """Structured request passed to forecast providers.

    Attributes:
        device_id: Unique device identifier.
        history: Ordered telemetry history used for model input.
        horizon: Number of future points to predict.
        metric_name: Metric name to forecast.
    """

    device_id: str
    history: list[TelemetrySample]
    horizon: int
    metric_name: str


@dataclass(slots=True)
class ForecastPoint:
    """One forecast result point.

    Attributes:
        timestamp: Timestamp label for the future point.
        predicted_value: Numeric predicted value.
        confidence_low: Optional lower bound.
        confidence_high: Optional upper bound.
    """

    timestamp: str
    predicted_value: float
    confidence_low: float | None = None
    confidence_high: float | None = None


@dataclass(slots=True)
class ForecastResult:
    """Normalized forecast output.

    Attributes:
        model_name: Provider model name.
        points: Predicted future points.
        metadata: Optional model execution metadata.
    """

    model_name: str
    points: list[ForecastPoint] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)


class ForecastProvider(ABC):
    """Abstract provider for time-series forecasting."""

    @abstractmethod
    async def forecast(self, request: ForecastRequest) -> ForecastResult:
        """Generate future points for a device metric.

        Args:
            request: Forecast request payload.

        Returns:
            Normalized forecast result.
        """


class NoopForecastProvider(ForecastProvider):
    """Placeholder forecast provider that preserves the extension contract."""

    async def forecast(self, request: ForecastRequest) -> ForecastResult:
        """Return an empty forecast response.

        Args:
            request: Forecast request payload.

        Returns:
            Empty forecast result with provider metadata.
        """
        return ForecastResult(
            model_name="noop",
            points=[],
            metadata={
                "device_id": request.device_id,
                "metric_name": request.metric_name,
                "message": "Attach a concrete forecast provider such as Prophet or ARIMA.",
            },
        )

