# API access control gap

Write endpoints require the configured ingestion key. For deployments with sensitive telemetry, set `SENTINELFORGE_PROTECT_READS=true` before starting the API. This requires the same `X-API-Key` header on `GET /events`, `GET /alerts`, `GET /metrics`, and `GET /alerts/{id}/activity`. Missing or invalid keys receive HTTP 401; a missing server-side key fails closed with HTTP 503. `GET /health` remains public for availability probes.

Read protection defaults to `false` to preserve the public, synthetic-data dashboard demo. This is **one shared-key access control**, not analyst-specific identities, scoped permissions, rate limiting, or an authenticated user session. Do not expose real organizational telemetry publicly without an authenticated gateway, TLS, role-based authorization, and operational key rotation. CORS only constrains browsers; it is not API authentication.
