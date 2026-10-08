# PROGRESS

## Current status (2026-10-08)

The full operator loop now runs in the app, which is Release 1 of the plan (implementation tasks 11–14):
- signal and opportunity: weather plus a Philippine commerce calendar;
- listing match and economics;
- brief, copy variants, policy checks, approval and export;
- results import and the assisted-versus-baseline overview.

All checks pass:
- pytest: 87 tests on SQLite and on PostgreSQL 18 (embedded);
- ruff check and ruff format;
- web lint, typecheck, test (8) and production build.

The whole flow was also verified in a browser on a scratch database with live Open-Meteo data.

Nothing is posted automatically. The operator confirms the listing, approves the copy, and posts. That is required by AGENTS.md and the plan.

**Action needed:** run `.venv\Scripts\python.exe -m pip install -e ".[dev]"` (adds `anthropic`) and `.venv\Scripts\python.exe -m alembic upgrade head` (migration 0004) before starting the API or worker.

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
- **PostgreSQL:** the full Python suite, migrations included, also passes on PostgreSQL 18. It was run locally with the embedded binaries. API test fixtures use `NullPool`, because asyncpg connections can't cross event loops.
- **CI:** added a GitHub Actions workflow running the Python matrix (SQLite and Postgres 17) and the web checks. It has not run on GitHub yet, because the repository has no remote.

## Round 3 (2026-10-08)
- **The threshold gate now filters.** Freshness and geography were both fixed at 100, so every timely score was at least 66, against a gate of 65.
  - Freshness is now `100 - 20 × lead_days`, so today scores 100 and 2 days out scores 60.
  - The default `MIN_TIMELY_SCORE` is now 70. Score version: `discovery-v2`.
  - Effect on the 3 cities: marginal rain 2 days out outside Manila is dropped. Forecast-only danger heat (42°C+) and hazard rain (50 mm+) also drop first, because of the medium-sensitivity penalty: 2 days out in Manila, and same-day or later in Cebu and Davao. This fits the plan's rule that high-impact alerts need official confirmation.
  - Tune with real data in Release 0.
- **Retirement no longer expires operator decisions.** When the forecast drops an event, only its `eligible` opportunities expire. Accepted, deferred, rejected and matched ones keep their own window.
- **A returning event reuses decided opportunities.** If the event comes back within that window, those opportunities are re-attached to the new event cluster instead of being duplicated as new eligible cards, so a rejection stays rejected.
- Tests: 54 Python (2 new; both fail on the old pipeline).

## Round 4 (2026-10-08): automating the product-to-post loop
- **Commerce calendar source** (`ph-calendar`, `calendar-rules-v1`):
  - it is computed, with nothing fetched;
  - it covers double-day sales (9.9 to 12.12 count as major), paydays on the 15th and 30th (or the month's last day), Valentine's, Mother's and Father's Day, back to school (June; DepEd caveat), and the Christmas gift season;
  - each occasion surfaces a fixed number of days ahead.
  - New needs: `sale_day_upgrades`, `gift_giving` and `school_supplies`, with 9 concepts (`needs-catalog-v2`).
  - Freshness now comes from the detector (`DetectedEvent.freshness`, moved to `intelligence/events.py`). Weather is unchanged at `100 - 20 × lead_days`. Calendar freshness only falls after 2 days out.
- **Listing match** (`opportunities/listings.py`, plan section 12):
  - Add a listing (marketplace, URLs, price, commission, seller, rating, reviews, sold, stock, verified facts, image provenance) once the opportunity is accepted.
  - Confirm it as live and affiliate-eligible. Out-of-stock and zero-commission listings are refused.
  - Confirming marks the previous confirmed listing `stale` and the opportunity `matched`.
  - Failed searches are logged with a reason.
- **Economics** (`scoring.py`):
  - `listing_economics` weighs commission amount (log scale, 50 at ₱20 per sale), price band, seller type, rating weighted by review count, and units sold.
  - `publish_priority` follows plan 9.5. Version `publish-v1`; the pipeline keeps it on reruns.
  - Today ranks by publish priority when present.
- **Studio** (`creative/`):
  - The brief comes from the listing and the concept: angle, audience, verified facts, claims to avoid, and the disclosure.
  - Generation produces 3 variants (problem, benefit and curiosity hooks): Claude `claude-opus-5-5` when `ANTHROPIC_API_KEY` is set, with structured output, effort `medium`, and server-side refusal fallbacks (`fallbacks="default"`); deterministic templates otherwise.
  - `policy.py` blocks prices and discounts, superlatives, urgency, health, safety and guarantee claims, fear framing, durability words, and numbers not in the verified facts.
  - Edits create a new variant. Approval is refused while blocking issues remain.
- **Export:**
  - It needs an approved variant and a listing re-confirmed within 72h (`LISTING_RECHECK_HOURS`).
  - It assigns a `t3xxxxxxxx` tracking code to use as the affiliate sub ID.
  - It always appends `AFFILIATE_DISCLOSURE`.
  - It returns the post text, links, and a checklist (sub ID, platform disclosure toggle, real product images, no price).
- **Results** (`results.py`):
  - CSV import with column aliases (`sub_id`, `commission`, …), ₱ and comma parsing, and ISO or MM/DD/YYYY dates.
  - It is append-only; unchanged re-imports are skipped.
  - Unknown codes count as baseline posts.
  - The overview shows assisted versus baseline posts by event type, category and hook, with sample-size warnings.
- **API:**
  - `POST /opportunities/{id}/product-match`, `POST /product-matches/{id}/confirm`, `POST /opportunities/{id}/search-failures`;
  - `GET /product-matches/{id}/studio`, `POST /product-matches/{id}/creative-brief`, `POST /creative-briefs/{id}/generate`;
  - `POST /creatives/{id}/review`, `POST|GET /creatives/{id}/export`;
  - `POST /results/import`, `GET /results/overview`.
  - Domain errors map to 404, 409, 422 and 502.
- **Web:** the listing section on the opportunity page, `/studio/[matchId]`, `/exports/[variantId]`, `/results`, and a Results nav link. Vitest resolves the `@/` alias.
- **Migration** `20261008_0004` is reversible: product_matches, listing_search_failures, creative_briefs, creative_variants, creative_reviews, metric_observations, and the score_snapshots economics and publish columns.
- **Copy eval:** `scripts/eval_copy.py` over `tests/fixtures/copy_briefs.json`. The template scores 15/15. **Claude has not been evaluated yet**: no API key was available in this session. Run the eval with a key before relying on AI copy, and record the result here.
- **Dependency:** `anthropic>=1.12,<2`, documented in pyproject.
- **Bugs found while testing in the browser:**
  - the "No affiliate listing has been matched yet" uncertainty stayed after a match;
  - the template wrote "a air fryer".

## Next
- **Before relying on AI copy:**
  - set `ANTHROPIC_API_KEY`;
  - run `scripts/eval_copy.py` and review the variants it prints;
  - record the pass rate here.
- **Affiliate APIs:** which programs (Shopee, Lazada, TikTok Shop, Involve Asia) and is API access approved? With access, add a listing adapter that pre-fills candidates from search phrases, and a report adapter that replaces the CSV import. Do not scrape.
- **Release 0:** run the loop with real posts for 2+ weeks (30+ posts if feasible), including baseline posts, then tune thresholds, catalog priors and economics weights from the results.
- **Creative Release 2** (after the Release 1 gate): templates and rendering that use the listing's real images, with fidelity checks. Then AI image or video editing (for example Veo through the Gemini API) only around the real product.
- **Not built:**
  - idempotency keys on generate, import and export (the UI disables buttons while pending);
  - a post URL or posted-at record;
  - model-run cost dashboard on `/operations` (token usage is stored on each variant's `generation`);
  - experiment assignment beyond a free-text label.
- **Still open from earlier reviews:**
  - Sign-in has no rate limiting. Use a long `OPERATOR_PASSWORD`, and add throttling before any public exposure.
  - `next.config.ts` uses `output: "standalone"`, so production should run `node .next/standalone/server.js`.
  - A missing opportunity returns HTTP 200 with the not-found UI, because `loading.tsx` streams before `notFound()`.
  - Push to GitHub to activate CI. There is no remote yet.
- **Product, per plan:** a labelled eval set before any AI classifier; a news source behind `DETECTORS`; a manual import path for concierge-collected signals.
