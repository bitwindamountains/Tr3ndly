# Tr3ndly

Tr3ndly is a Philippines-focused affiliate opportunity intelligence system. This repository contains the foundation and the first automated evidence-to-opportunity slice. A worker pulls Open-Meteo forecasts for Metro Manila, Cebu City and Davao City and detects heat and heavy-rain events. It turns them into consumer needs and generic product concepts, scores them, and fills the Today queue for operator review.

## Local setup

### API

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe scripts\seed_demo.py
.venv\Scripts\python.exe -m uvicorn apps.api.app.main:app --reload
```

The default local database is SQLite so development works without Docker. Set `DATABASE_URL` to an async PostgreSQL URL for shared or deployed environments.

### Worker

```powershell
.venv\Scripts\python.exe -m tr3ndly.worker          # polls due sources every WORKER_TICK_SECONDS
.venv\Scripts\python.exe -m tr3ndly.worker --once   # run enabled sources now, then exit (cron or Task Scheduler)
```

Run exactly one worker per database. Each run is recorded and can be inspected at `GET /operations/runs`; source health is at `GET /operations/sources`. Once any run succeeds, Today switches from demo to live mode and hides the seeded demo card.

Open-Meteo's free API is for non-commercial use. In production, set `OPEN_METEO_API_KEY`; the app refuses to start without it. Attribution (CC BY 4.0) is shown in the Today footer.

### Web

```powershell
npm.cmd install
npm.cmd run dev:web
```

Open http://localhost:3000. The API runs at http://localhost:8000 and exposes OpenAPI documentation at http://localhost:8000/docs.

## Checks

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
npm.cmd run lint:web
npm.cmd run typecheck:web
npm.cmd run test:web
npm.cmd run build:web
```

## Configuration

Copy `.env.example` to `.env` and adjust it. Do not commit `.env`.
