# CLAUDE.md

Guidance for Claude Code in this repository. Product and engineering rules live in [AGENTS.md](AGENTS.md); read it too.

@AGENTS.md

Tr3ndly is a Philippines-focused affiliate opportunity intelligence system. It is a modular monolith:
- **API:** FastAPI app in `apps/api/app` (thin routes only).
- **Domain:** Python package `tr3ndly/` (all logic).
- **Worker:** one process, `tr3ndly.worker`.
- **Web:** Next.js 16 in `apps/web`.
- **Database:** SQLite by default; set `DATABASE_URL` for async PostgreSQL.

The plans are [docs/dev-notes/master-build-plan.md](docs/dev-notes/master-build-plan.md) (newer, v2.0, wins on conflict) and [docs/dev-notes/system-architecture.md](docs/dev-notes/system-architecture.md).

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
npm.cmd run lint:web ; npm.cmd run typecheck:web ; npm.cmd run test:web ; npm.cmd run build:web
.venv\Scripts\python.exe scripts\eval_copy.py   # copy policy pass rate over tests/fixtures/copy_briefs.json
```

CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs ruff and pytest on both SQLite and PostgreSQL 17, plus the web lint, typecheck, test and build. Set `TEST_DATABASE_URL=postgresql+asyncpg://...` to run the Python suite on Postgres locally; the fixtures reset the `public` schema before each test. `tests/db/test_migrations.py` runs upgrade, downgrade, upgrade, and a drift check on whichever database is configured.

On Windows without Docker, you can borrow the rental manager's embedded Postgres binaries (`../rental manager/node_modules/@embedded-postgres/windows-x64/native/bin`): use `initdb` and `pg_ctl` on a spare port.

## Architecture

**Pipeline** ([tr3ndly/pipeline.py](tr3ndly/pipeline.py)). One source run is: fetch → normalize → exact dedupe → detect events → threshold gate → needs → product concepts → score. Each run writes a `source_runs` row with stats or an error. The pipeline never changes an operator decision. Each run also retires events that the latest data no longer supports; that expires only undecided (eligible) opportunities, and a returning event re-attaches the decided ones instead of duplicating them.

**Sources** (`tr3ndly/sources/`). Adapters implement `fetch` and `normalize` only: no persistence and no AI. Each `SourceDefinition` declares its licence, attribution URL, poll interval and confidence. They are registered in `build_adapters()`. `ENABLED_SOURCES` (comma-separated, default `open-meteo,ph-calendar`) decides which ones run. Open-Meteo's free API is non-commercial, so production refuses it without `OPEN_METEO_API_KEY`. `ph-calendar` is computed (sale days, paydays, gifting and school seasons); nothing is fetched.

**Intelligence** (`tr3ndly/intelligence/`):
- `weather_rules.py` and `calendar_rules.py` map facts to `DetectedEvent`s (`events.py`) deterministically. Each detector sets its own `freshness`: a forecast loses 20 per day out, a calendar date only after two days out.
- `catalog.py` maps needs to generic product concepts. These are never SKUs.
- `scoring.py` holds the plan formulas: timely score, discovery priority, and, once a listing is confirmed, listing economics (9.3) and publish priority (9.5, version `publish-v1`).
- `DETECTORS` maps a source slug to its detector; an AI classifier plugs in here later.

Rules, the catalog, and the score each carry a version string. Bump it when behaviour changes. Score snapshots store `components` so a formula can be replayed.

**Data rules:**
- All datetimes use `UTCDateTime` ([tr3ndly/db/types.py](tr3ndly/db/types.py)). Never pass naive datetimes.
- Migrations must be reversible. SQLite needs `op.batch_alter_table`.
- Evidence, score snapshots, decisions, creative reviews, and metric observations are append-only. Copy edits create a new variant.
- Money is integer centavos and commission rates are basis points; the API converts to PHP and percent.

**Opportunities** (`tr3ndly/opportunities/`):
- `queries.py` is the read side.
- `decisions.py` (operator decisions) and `listings.py` (product matches, failed searches) are the write side and hold the state rules. Listings need an accepted or matched opportunity. Confirming one marks older confirmed listings `stale`, sets the opportunity to `matched`, and rescores it.
- `scores.py` appends score snapshots for both the pipeline and listing confirmation.
- `views.py` maps ORM rows to schemas.

**Creative** (`tr3ndly/creative/`): `studio.py` handles briefs, generation, review and export. `policy.py` holds the deterministic claim checks; blocking issues prevent approval. `copywriter.py` uses `ClaudeCopywriter` when `ANTHROPIC_API_KEY` is set (structured output plus server-side refusal fallbacks) and `TemplateCopywriter` otherwise. The prompt in `prompts.py` is versioned (`COPY_PROMPT_VERSION`): run `scripts/eval_copy.py` before bumping it. Export needs an approved variant and a listing re-confirmed within `LISTING_RECHECK_HOURS`. It assigns a `t3…` tracking code for the affiliate sub ID and always appends `AFFILIATE_DISCLOSURE`.

**Results** ([tr3ndly/results.py](tr3ndly/results.py)): CSV import keyed by tracking code and day, where the newest row wins. Codes Tr3ndly did not issue count as baseline posts. The overview splits assisted and baseline posts and groups them by category, event type and hook.

**Errors.** Domain code raises `NotFound`, `Conflict`, `InvalidInput` or `UpstreamError` ([tr3ndly/errors.py](tr3ndly/errors.py)), and `main.py` maps them to 404, 409, 422 and 502.

**Today.** It is in live mode once any source run has succeeded, and then demo cards are hidden. It ranks by publish priority when present, otherwise by discovery priority. It shows at most 2 cards per event and 8 in total, plus the top 3 signals. It takes optional `location` and `reason_type` filters. `source_health` is derived from run recency; see [tr3ndly/operations.py](tr3ndly/operations.py).

**Auth (deny by default once configured):**
- **API.** Every route except `/health` sits on the `protected` router (`apps/api/app/auth.py`). When `OPERATOR_TOKEN` is set, those routes require it as a bearer token. Production refuses to start without a token of 32+ characters. There is no CORS: only the Next.js server calls the API.
- **Web.** Only `lib/api.ts` (marked `server-only`) talks to the API, using `API_OPERATOR_TOKEN`. Web env lives in `apps/web/.env.local`; see `apps/web/.env.example`.
- **Operator sign-in.** Setting `OPERATOR_PASSWORD` enables it. `SESSION_SECRET` signs an HMAC cookie (`lib/session.ts`). `proxy.ts` (Next 16's name for middleware) gates pages.
- **Server actions.** Every one in `app/actions.ts` must call `assertOperator()` first, because server actions are reachable by direct POST.
- **Domain rules stay server-side.** For example, the API returns `decidable` and the UI never recomputes it.

**Next 16 specifics.** `error.tsx` receives `retry`, not `reset`. Use `refresh()` from `next/cache` after mutations. The `react-hooks/purity` lint rule forbids `Date.now()` during render. Server actions cap request bodies at 1MB. Read `node_modules/next/dist/docs/` before using a Next API. Web pages: `/` (Today), `/opportunities/[id]` (decision and listings), `/studio/[matchId]`, `/exports/[variantId]`, `/results`, `/operations`.

**Philippine time.** `tr3ndly.geo.MANILA` is a fixed UTC+8 offset. The Philippines has no DST, and Windows Python has no tzdata.

## Session workflow
- At the start of each session, read [docs/dev-notes/PROGRESS.md](docs/dev-notes/PROGRESS.md) for the current status and next steps.
- After any major or relevant change, update docs/dev-notes/PROGRESS.md with what was done and what's next. Major changes include a new feature, an architecture change, an important decision, a bug fix, or a new command.
- If the change affects lasting project knowledge (structure, setup, commands, conventions), also update this file.
- Keep this file concise and put task-specific detail in docs/dev-notes/PROGRESS.md.
- Before the user runs /clear or /compact, make sure both files are up to date.
