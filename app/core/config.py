"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _parse_bool(value: str | None, default: bool) -> bool:
    """Parse a boolean environment variable.

    Args:
        value: Raw environment variable value.
        default: Fallback value when parsing fails.

    Returns:
        Parsed boolean value.
    """
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _parse_int(value: str | None, default: int, *, minimum: int = 0) -> int:
    """Parse an integer environment variable with lower bound protection.

    Args:
        value: Raw environment variable value.
        default: Fallback value when parsing fails.
        minimum: Minimum accepted value.

    Returns:
        Parsed integer value.
    """
    try:
        parsed = int(value) if value is not None else default
    except ValueError:
        parsed = default
    return max(minimum, parsed)


def _parse_float(value: str | None, default: float, *, minimum: float = 0.0) -> float:
    """Parse a float environment variable with lower bound protection.

    Args:
        value: Raw environment variable value.
        default: Fallback value when parsing fails.
        minimum: Minimum accepted value.

    Returns:
        Parsed float value.
    """
    try:
        parsed = float(value) if value is not None else default
    except ValueError:
        parsed = default
    return max(minimum, parsed)


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable runtime settings for the backend service.

    Attributes:
        app_name: Display name of the service.
        app_version: Application semantic version.
        api_prefix: Shared API prefix for all public routes.
        host: Host interface used by the ASGI server.
        port: Port used by the ASGI server.
        debug: Whether debug mode is enabled.
        log_level: Root log level name.
        database_url: Database connection string reserved for persistence modules.
        history_storage_backend: Selected history storage backend.
        max_connections: Maximum active device connections allowed by the pool.
        queue_maxsize: Maximum number of buffered telemetry events.
        stream_batch_size: Maximum number of telemetry records per flush batch.
        stream_flush_interval_seconds: Maximum flush interval for buffered telemetry.
        telemetry_retention_per_device: Retained history events per device in memory.
        default_history_limit: Default query limit for history APIs.
        default_forecast_horizon: Default number of future points for forecast APIs.
        forecast_provider: Forecast provider identifier used by dependency wiring.
    """

    app_name: str
    app_version: str
    api_prefix: str
    host: str
    port: int
    debug: bool
    log_level: str
    database_url: str
    history_storage_backend: str
    max_connections: int
    queue_maxsize: int
    stream_batch_size: int
    stream_flush_interval_seconds: float
    telemetry_retention_per_device: int
    default_history_limit: int
    default_forecast_horizon: int
    forecast_provider: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Build and cache runtime settings from environment variables.

    Returns:
        Parsed application settings.
    """
    return Settings(
        app_name=os.getenv("APP_NAME", "Energy-Grid-Core").strip() or "Energy-Grid-Core",
        app_version=os.getenv("APP_VERSION", "0.0.0.1").strip() or "0.0.0.1",
        api_prefix=os.getenv("API_PREFIX", "/api/v1").strip() or "/api/v1",
        host=os.getenv("APP_HOST", "0.0.0.0").strip() or "0.0.0.0",
        port=_parse_int(os.getenv("APP_PORT"), 8000, minimum=1),
        debug=_parse_bool(os.getenv("APP_DEBUG"), False),
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
        database_url=os.getenv("DATABASE_URL", "sqlite:///./energy_grid_core.db").strip()
        or "sqlite:///./energy_grid_core.db",
        history_storage_backend=os.getenv("HISTORY_STORAGE_BACKEND", "sqlalchemy").strip().lower()
        or "sqlalchemy",
        max_connections=_parse_int(os.getenv("MAX_DEVICE_CONNECTIONS"), 1000, minimum=1),
        queue_maxsize=_parse_int(os.getenv("STREAM_QUEUE_MAXSIZE"), 50000, minimum=1),
        stream_batch_size=_parse_int(os.getenv("STREAM_BATCH_SIZE"), 500, minimum=1),
        stream_flush_interval_seconds=_parse_float(
            os.getenv("STREAM_FLUSH_INTERVAL_SECONDS"),
            1.0,
            minimum=0.1,
        ),
        telemetry_retention_per_device=_parse_int(
            os.getenv("TELEMETRY_RETENTION_PER_DEVICE"),
            1000,
            minimum=1,
        ),
        default_history_limit=_parse_int(os.getenv("DEFAULT_HISTORY_LIMIT"), 200, minimum=1),
        default_forecast_horizon=_parse_int(
            os.getenv("DEFAULT_FORECAST_HORIZON"),
            24,
            minimum=1,
        ),
        forecast_provider=os.getenv("FORECAST_PROVIDER", "noop").strip() or "noop",
    )
