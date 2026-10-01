# Tr3ndly repository guidance

## Architecture

- Keep the application a modular monolith: Next.js web, FastAPI API, one worker, PostgreSQL-compatible persistence.
- Domain decisions live in backend services, not route handlers or React components.
- External providers must sit behind typed adapters.
- Manual import and export paths remain supported.

## Product rules

- Every opportunity must retain evidence, freshness, uncertainty, and score version.
- Timely events produce consumer needs before product concepts.
- Do not create exact-product content before an operator confirms a real affiliate listing.
- Never bypass human approval or generate unsupported product claims.
- Do not scrape marketplaces or publishers without explicit permission and compatible terms.

## Engineering rules

- TypeScript and Python type checking stay strict.
- Migrations must be reversible.
- AI prompts and output schemas are versioned and evaluated.
- Secrets never enter source control or browser bundles.
- Add tests for behavior changes and fixture tests for external adapters.
- Do not add a dependency without documenting why it is needed.

## Commands

```text
npm run dev:web
npm run build:web
npm run typecheck:web

.venv/Scripts/python -m uvicorn apps.api.app.main:app --reload
.venv/Scripts/python -m pytest
.venv/Scripts/python -m ruff check .
```

