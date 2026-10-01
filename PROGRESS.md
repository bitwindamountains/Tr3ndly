# PROGRESS

## Current status (2026-10-02)

The automated evidence-to-opportunity loop works end to end against live Open-Meteo data. This is Phase C of the master plan, implementation tasks 4–6 and 9, at version 0.2.0. All checks pass:
- pytest (43 tests);
- ruff check and ruff format;
- web typecheck, lint, test and production build.

**Action needed:** the local `tr3ndly.db` is still at migration 0002. Run `.venv\Scripts\python.exe -m alembic upgrade head` before starting the API or worker.

A pre-refactor backup was taken because this folder is not a git repository. It is the session-scoped scratchpad file `affiliate-backup-before-refactor.tgz`. Consider running `git init` and making a baseline commit.

## Done (2026-10-02)

### Review findings fixed
- **Datetimes came back naive from SQLite.** JSON had no offset, so browsers shifted times by 8h. Fixed with the `UTCDateTime` type.
- **SQLite foreign-key pragma.** It was registered on every engine and checked the app URL. It is now per-engine and checks the dialect.
- **Schema drift.** The `source_configs.slug` index did not match between models and migrations, so `alembic check` failed. Fixed in migration 0003.
- **No exact dedupe.** Migration 0002 dropped the hash constraint. There is now a unique `(source_id, content_hash)`.
- **`/today` health.** It always said `healthy` in live mode. It is now derived from source run recency.
- **Missing score snapshot.** An opportunity without one gave a 500. It is now skipped on Today and returns 404 on detail.
- **Decisions on closed opportunities.** They were allowed on expired or matched opportunities and after the window closed. These now return 409.
- **Dependency inversion.** The domain imported API schemas. Schemas, settings and logging moved into `tr3ndly/`.
- **Second-precision `created_at`.** "Latest score" could be random. It now uses a Python-side microsecond default.
- **Web fallback demo ID.** It (`opp_demo_fan`) did not match the API (`demo_opp_fan`).
- **API outages showed as 404 on the detail page.** They now show `error.tsx` with retry. Next 16 uses the `retry` prop, not `reset`.
- **Opportunity grid broke with more than one card.** "1 evidence item" is now pluralized, and times display in PHT.

### Automation added
- **Source contract** (`tr3ndly/sources/base.py`): `SourceDefinition` registry facts, `NormalizedSignal` with a content hash, and retries with backoff and jitter. 429 and 5xx responses are retried; other 4xx are not.
- **Open-Meteo adapter.** One request covers 3 PH cities and 3 forecast days. With a key it uses the commercial endpoint, and production refuses to run without one.
- **Weather rules** (`weather-rules-v1`):
  - HEAT triggers at a feels-like temperature of 38°C or more. At 42°C or more, sensitivity becomes medium with a "no health claims" caveat.
  - HEAVY_RAIN triggers at 20 mm or more with a probability of 60% or more. At 50 mm or more, sensitivity becomes medium with a "confirm with PAGASA" caveat.
  - An event expires at midnight Manila time after its last qualifying day.
- **Catalog** (`needs-catalog-v1`): 6 needs mapped to 9 generic concepts, each with search queries, claims to avoid, and execution and marketplace-fit priors.
- **Scoring** (`discovery-v1`): plan formulas 9.1, 9.5 and combined demand. Snapshots store the components so they can be replayed, and a new snapshot is written only when the score changes.
- **Pipeline** (`tr3ndly/pipeline.py`):
  - idempotent upserts of event clusters, opportunities, and evidence linked to raw signals;
  - a threshold gate, `MIN_TIMELY_SCORE=65`;
  - retirement of events the latest forecast drops;
  - expiry sweeps;
  - operator decisions are never changed.
- **Worker** (`python -m tr3ndly.worker`, `--once`, `--source`, `tr3ndly-worker` script):
  - polls each source on its interval (3h for Open-Meteo);
  - retries after 15 min on failure;
  - skips sources that are already running;
  - fails runs abandoned for more than 30 min.
- **API:**
  - `/today` returns `sources`, the real top 3 signals, live or demo mode (demo cards are hidden once live), and a limit of 2 cards per event and 8 in total.
  - New read-only `GET /operations/sources` and `GET /operations/runs`.
- **Web:** a degraded-source banner, a source attribution and health footer, a score-breakdown card, and linked evidence.
- **Migration** `20261002_0003` is reversible; `tests/db/test_migrations.py` checks upgrade, downgrade, upgrade and drift.
- `httpx` is now a runtime dependency (documented in pyproject). New env vars are listed in `.env.example`.

### Verified live
`--once` against real Open-Meteo created 3 HEAT events (Manila, Cebu, Davao) and 12 opportunities. A rerun found 9 duplicates and 0 new rows. The API and the built web app rendered the live queue and detail pages.

## Round 2 (2026-10-02)
- **git:** initialized the repository on `main`. `d9bfb34` is the pre-refactor baseline and `f617d1b` is the automation refactor. `.gitattributes` forces LF line endings to match `.editorconfig`.
- **Refactor:**
  - The pipeline is a per-run `_Ingestion` class, replacing functions that took eight parameters.
  - Opportunity scoring moved to `scoring.score_concept`.
  - `SourceDefinition.attribution_url` replaces a hard-coded Open-Meteo check.
  - The repository is split into `queries.py`, `decisions.py` and `views.py`.
  - Evidence is grouped by the raw signal's external id instead of by parsing the summary string.
- **Feature:** `/today` takes `?location=` and `?reason_type=` and returns `locations` for filter controls.
- **Auth:**
  - The API takes an `OPERATOR_TOKEN` bearer token on all routes except `/health`. Production refuses to start without a token of 32+ characters. CORS is removed.
  - The web app has single-operator sign-in: an HMAC-signed httpOnly cookie, the `proxy.ts` gate, and `/login`.
  - Decisions go through a server action that checks the session and calls the API server-side, so the token never reaches the browser. The new dependency is `server-only`.
- **Web:**
  - a shared header with working Today and Operations nav plus sign-out; the dead buttons are removed;
  - location and reason filter chips on Today;
  - a `/operations` page listing sources and recent runs;
  - the decision panel is disabled when the API says the opportunity is not `decidable`;
  - dependencies are pinned (they were `latest`).
- **Verified end to end** on a scratch database with auth on:
  - the API returns 401 without the token;
  - anonymous visits, forged cookies, and direct server-action POSTs are redirected to `/login`;
  - invalid action input is rejected;
  - in real Chrome: wrong password, sign-in, Operations, filtering by Cebu, Defer (recorded and shown in the audit trail), and sign-out all worked.
- **Tests:** 52 Python and 6 web.

## Next
- **Not fixed: open review items.**
  - Sign-in has no rate limiting. Use a long `OPERATOR_PASSWORD`, and add throttling before any public exposure.
  - `next.config.ts` uses `output: "standalone"`, so production should run `node .next/standalone/server.js` rather than `next start`.
  - A missing opportunity returns HTTP 200 with the not-found UI, because `loading.tsx` streams before `notFound()`.
  - There is no CI workflow. Add GitHub Actions for pytest, ruff, the migration test and the web checks.
- **Product, per plan:**
  - Add a `/operations` page using the new endpoints.
  - Release 0 validation with a real operator, to tune thresholds and catalog priors.
  - Build a labelled eval set before any AI classifier.
  - Add a news source behind `DETECTORS`.
  - Product match and failed-search logging (task 11), then listing economics (task 12).
  - A manual import path for concierge-collected signals.
