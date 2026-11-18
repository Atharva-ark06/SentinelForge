# Operations and reliability

- **Liveness**: `GET /health` checks the API and SQLite using `SELECT 1`; returns HTTP 503 on database failure.
- **API docs**: `GET /docs` (Swagger UI) and `GET /redoc` when `SENTINELFORGE_ENABLE_DOCS=true`.
- **Request IDs**: each HTTP response includes `X-Request-ID`; JSON logs contain request ID, UTC timestamp, path (not query string), method, status, and duration. Avoid sending secrets in URL paths.
- **Compression**: responses of at least 1 KiB may be gzip-compressed when the client advertises support.
- **Caching**: API telemetry uses `Cache-Control: no-store`; static HTML may use `no-cache` so browsers revalidate.
- **Shutdown**: Uvicorn handles SIGINT/SIGTERM; FastAPI lifespan teardown logs shutdown and the SQLite helpers close per-operation connections.
- **Pagination**: `/events` and `/alerts` accept bounded `limit` and `offset`; `/alerts/{id}/activity` is also bounded.
- **Pre-commit**: `pip install pre-commit && pre-commit install && pre-commit run --all-files`. Hooks include Ruff and Gitleaks. Review hook changes before committing.
- **Seed**: `python -m scripts.seed --db sentinelforge-demo.sqlite3` generates synthetic events in a separate database. `--force` appends to an existing DB.
- **Dependabot**: pip, npm, and GitHub Actions update rules are already configured in `.github/dependabot.yml`.
