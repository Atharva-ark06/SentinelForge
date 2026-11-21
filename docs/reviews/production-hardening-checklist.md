# Production hardening acceptance checklist

This checklist separates implemented controls from deployment prerequisites.
A static GitHub Pages application does not provide authentication to a remote API.

## Browser and frontend
- [x] Theme control on the deployed React entrypoint, with persisted preference.
- [x] Clearly labelled in-memory synthetic preview; it never sends ingest requests.
- [x] Ignore late API responses after switching to synthetic preview.
- [ ] Verify keyboard and screen-reader flows in a real browser.
- [ ] Verify frontend build and lockfile audit in CI.

## API
- [x] Explicit CORS origins; do not rely on CORS for authentication.
- [x] Ingestion requires a configured secret; comparisons must be timing-safe.
- [x] Input validation for event ingestion and query pagination.
- [ ] Add an authenticated user gateway and authorization roles before real telemetry.
- [ ] Enforce TLS and persistent database backups at the deployment platform.

## Operational validation
- [ ] Run complete GitHub Actions suite only after the 200-commit target.
- [ ] Review dependency audit results and fix high/critical advisories.
- [ ] Confirm deployed frontend uses a reachable HTTPS API origin.
- [ ] Test rate limits, backend downtime, and retry behavior.
- [ ] Confirm that no credentials are exposed in Vite environment variables.
- [ ] Update root README as the last content commit.

## Data classification
Synthetic examples use RFC 5737 documentation addresses. Do not treat them as
real incidents or persist them into production databases.
