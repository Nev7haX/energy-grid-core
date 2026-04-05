# Energy-Grid-Core

[简体中文详细说明](README.zh-CN.md)

Energy-Grid-Core is a modular backend foundation for energy monitoring and device state management. It is designed as a clean, reusable architecture skeleton for teams that need to build telemetry-heavy backend services with clear separation between device connectivity, realtime ingestion, historical persistence, and forecast integration.

## What This Repository Provides

- device connection pool management
- realtime telemetry ingestion pipeline
- historical data storage abstraction with a default SQLAlchemy implementation
- pluggable forecast provider interface
- FastAPI-based API surface for monitoring, history, and forecast workflows

## Architecture Highlights

- **High-concurrency ingestion**: telemetry is buffered through a bounded `asyncio.Queue` and flushed in batches.
- **Modular boundaries**: API, core infrastructure, models, and services are separated for maintainability.
- **Storage abstraction**: history persistence is exposed through `HistoryStoragePort`, making backend replacement straightforward.
- **Forecast extensibility**: forecast integration is isolated behind `ForecastProvider`, so concrete models can be added without rewriting API handlers.

## Default Stack

- Python `3.11`
- FastAPI
- SQLAlchemy 2.0
- SQLite for local development
- pytest + httpx for verification

## Project Layout

```text
project-root/
├── app/
│   ├── api/             # Route layer
│   ├── core/            # Runtime config, lifecycle, logging, errors
│   ├── models/          # ORM models
│   └── services/        # Business and infrastructure services
├── tests/               # Automated tests
├── .env.example         # Environment variable template
├── pyproject.toml
├── requirements.txt
└── main.py
```

## API Surface

- `POST /api/v1/devices/connect`
- `DELETE /api/v1/devices/{device_id}`
- `POST /api/v1/monitoring/ingest`
- `GET /api/v1/monitoring/overview`
- `GET /api/v1/history/{device_id}`
- `POST /api/v1/forecast/{device_id}`

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --host 0.0.0.0 --port 8000
```

Run tests:

```bash
source .venv/bin/activate
pytest
```

## Configuration

Runtime settings are environment-driven. The default `.env.example` uses:

- `APP_VERSION=0.0.0.1`
- `HISTORY_STORAGE_BACKEND=sqlalchemy`
- `DATABASE_URL=sqlite:///./energy_grid_core.db`

## Repository Notes

- This repository is prepared for public source visibility on GitHub.
- No hardcoded secrets or environment-specific endpoints are included.
- Local artifacts such as `.env`, `.venv`, `.DS_Store`, and SQLite database files are ignored.
- Dependencies are pinned to tested versions for reproducible setup.

## License

See [LICENSE](LICENSE).

The current repository license state is `All rights reserved`, which means the source is visible but not published as an open-source licensed codebase.
