# Update an alert status

Use `PATCH /alerts/{alert_id}/status` with a JSON body containing `status`, `actor`, and optional `note`. The endpoint requires `X-API-Key`; it returns 401 for a wrong key and 503 if write operations are disabled because no key is configured. Invalid payloads or transitions return 422, and unknown alert IDs return 404.

The static browser app must not embed the shared API key. Use the trusted CLI or another server-side client.