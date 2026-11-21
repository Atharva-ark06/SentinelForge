# Live dashboard data audit

## Architecture and deployment constraints

The React frontend is a static application. GitHub Pages does not run FastAPI or SQLite. Therefore a Pages deployment without a separately hosted, reachable API cannot display live events, alerts, or metrics.

## Required checks

1. Identify the deployed dashboard URL and inspect its network requests for `/health`, `/metrics`, `/events`, and `/alerts`.
2. Confirm `VITE_API_BASE_URL` points to the HTTPS FastAPI deployment at build time; do not point it at a GitHub Pages origin.
3. Verify the API's `SENTINELFORGE_ALLOWED_ORIGINS` contains the exact dashboard origin.
4. Verify `SENTINELFORGE_ALLOWED_HOSTS` contains the deployed API hostname.
5. Verify read authorization: public demo deployments should expose synthetic data only; private telemetry requires `SENTINELFORGE_PROTECT_READS=true`.
6. Validate browser CORS preflight, health checks, JSON response shapes, and request error states.
7. Never bundle an ingestion API key in the static frontend.

## Synthetic demonstration policy

Synthetic data must be visibly labeled **Demo data** and must never be represented as real SOC telemetry. Use reserved example IP address ranges (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`) and fictitious hostnames. Do not auto-ingest demo events into a real backend. Prefer an explicit, reversible demo-mode toggle in the frontend when no API is configured.

## Acceptance criteria

- Empty database: intentional empty state, not a broken spinner.
- Unreachable API: informative error with retry.
- Demo mode: realistic alerts and metrics, clear persistent demo label.
- Live mode: fetches only configured API and never silently falls back to demo.
- Refresh and navigation preserve selected mode and avoid stale response overwrites.
