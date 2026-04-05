"""Application entrypoint for Energy-Grid-Core."""

from __future__ import annotations

from fastapi import FastAPI

from app.api.routes_devices import router as devices_router
from app.api.routes_forecast import router as forecast_router
from app.api.routes_history import router as history_router
from app.api.routes_monitoring import router as monitoring_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.lifecycle import create_lifespan
from app.core.logging import configure_logging
from app.core.responses import success_response


def create_app() -> FastAPI:
    """Create the FastAPI application instance.

    Args:
        None.

    Returns:
        Configured FastAPI application.
    """
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=create_lifespan(settings),
    )
    register_exception_handlers(app)
    app.include_router(devices_router, prefix=settings.api_prefix)
    app.include_router(monitoring_router, prefix=settings.api_prefix)
    app.include_router(history_router, prefix=settings.api_prefix)
    app.include_router(forecast_router, prefix=settings.api_prefix)

    @app.get("/", summary="Service index")
    async def index() -> dict[str, object]:
        """Return a lightweight index payload.

        Args:
            None.

        Returns:
            Service metadata payload.
        """
        return success_response(
            {
                "service": settings.app_name,
                "version": settings.app_version,
                "api_prefix": settings.api_prefix,
            },
            message="service ready",
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    runtime_settings = get_settings()
    uvicorn.run(
        "main:app",
        host=runtime_settings.host,
        port=runtime_settings.port,
        reload=runtime_settings.debug,
    )
