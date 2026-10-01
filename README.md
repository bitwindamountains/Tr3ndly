# Tr3ndly

Tr3ndly is a Philippines-focused affiliate opportunity intelligence system. This repository currently contains the foundation and the first evidence-to-opportunity demo slice.

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
npm.cmd run typecheck:web
npm.cmd run test:web
npm.cmd run build:web
```

## Configuration

Copy `.env.example` to `.env` and adjust it. Do not commit `.env`.
