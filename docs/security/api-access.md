# API access control gap

Write endpoints currently require the configured ingestion key. Read endpoints `GET /events` and `GET /alerts` currently do not. CORS only constrains browser behavior and does not block direct clients. Until authenticated read access and authorization are implemented, do not expose sensitive telemetry through a public API.