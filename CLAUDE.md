# CLAUDE.md

Guidance for Claude Code in this repository. Product and engineering rules live in [AGENTS.md](AGENTS.md); read it too.

@AGENTS.md

Tr3ndly is a Philippines-focused affiliate opportunity intelligence system. It is a modular monolith:
- **API:** FastAPI app in `apps/api/app` (thin routes only).
- **Domain:** Python package `tr3ndly/` (all logic).
- **Worker:** one process, `tr3ndly.worker`.
- **Web:** Next.js 16 in `apps/web`.
- **Database:** SQLite by default; set `DATABASE_URL` for async PostgreSQL.

The plans are [TR3NDLY_MASTER_BUILD_PLAN.md](TR3NDLY_MASTER_BUILD_PLAN.md) (newer, v2.0, wins on conflict) and [TR3NDLY_SYSTEM_ARCHITECTURE.md](TR3NDLY_SYSTEM_ARCHITECTURE.md).

## Commands (Windows, from repo root)

```powershell
.venv\Scripts\python.exe -m pip install -e ".[dev]"
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe scripts\seed_demo.py              # optional demo card
.venv\Scripts\python.exe -m uvicorn apps.api.app.main:app --reload   # :8000, docs at /docs
.venv\Scripts\python.exe -m tr3ndly.worker                 # scheduler loop
.venv\Scripts\python.exe -m tr3ndly.worker --once          # run enabled sources now and exit
npm.cmd run dev:web                                        # :3000
```

Checks:

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check . ; .venv\Scripts\python.exe -m ruff format --check .
npm.cmd run typecheck:web ; npm.cmd run test:web ; npm.cmd run build:web
```

To check for schema drift, run `alembic check` against a freshly upgraded database. `tests/db/test_migrations.py` runs upgrade, downgrade, upgrade, and a drift check.

## Architecture

**Pipeline** ([tr3ndly/pipeline.py](tr3ndly/pipeline.py)). One source run is: fetch → normalize → exact dedupe → detect events → threshold gate → needs → product concepts → score. Each run writes a `source_runs` row with stats or an error. The pipeline never changes an operator decision. Each run also retires events that the latest data no longer supports.

**Sources** (`tr3ndly/sources/`). Adapters implement `fetch` and `normalize` only: no persistence and no AI. Each `SourceDefinition` declares its licence, attribution URL, poll interval and confidence. They are registered in `build_adapters()`. `ENABLED_SOURCES` (comma-separated) decides which ones run. Open-Meteo's free API is non-commercial, so production refuses it without `OPEN_METEO_API_KEY`.

**Intelligence** (`tr3ndly/intelligence/`):
- `weather_rules.py` maps forecast facts to events deterministically.
- `catalog.py` maps needs to generic product concepts. These are never SKUs.
- `scoring.py` holds the plan formulas.
- `DETECTORS` maps a source slug to its detector; an AI classifier plugs in here later.

Rules, the catalog, and the score each carry a version string. Bump it when behaviour changes. Score snapshots store `components` so a formula can be replayed.

**Data rules:**
- All datetimes use `UTCDateTime` ([tr3ndly/db/types.py](tr3ndly/db/types.py)). Never pass naive datetimes.
- Migrations must be reversible. SQLite needs `op.batch_alter_table`.
- Evidence, score snapshots, and decisions are append-only.

**Opportunities** (`tr3ndly/opportunities/`):
- `queries.py` is the read side.
- `decisions.py` is the write side and holds the state rules.
- `views.py` maps ORM rows to schemas.

**Today.** It is in live mode once any source run has succeeded, and then demo cards are hidden. It shows at most 2 cards per event and 8 in total, plus the top 3 signals. It takes optional `location` and `reason_type` filters. `source_health` is derived from run recency; see [tr3ndly/operations.py](tr3ndly/operations.py).

**Philippine time.** `tr3ndly.geo.MANILA` is a fixed UTC+8 offset. The Philippines has no DST, and Windows Python has no tzdata.

## Session workflow
- At the start of each session, read [PROGRESS.md](PROGRESS.md) for the current status and next steps.
- After any major or relevant change, update PROGRESS.md with what was done and what's next. Major changes include a new feature, an architecture change, an important decision, a bug fix, or a new command.
- If the change affects lasting project knowledge (structure, setup, commands, conventions), also update this file.
- Keep this file concise and put task-specific detail in PROGRESS.md.
- Before the user runs /clear or /compact, make sure both files are up to date.
