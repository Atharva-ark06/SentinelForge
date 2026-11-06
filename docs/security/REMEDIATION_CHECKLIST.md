# Security remediation implementation checklist

This file tracks the remediation work associated with [issue #17](../../issues/17). It is a **work plan, not evidence that controls are already implemented**. Each item must be verified against code, automated tests, and the actual deployment before being marked complete.

- [ ] Confirm the API rejects POST /events when X-API-Key is absent.
- [ ] Confirm the API rejects POST /demo/run when X-API-Key is absent.
- [ ] Confirm incorrect API keys return HTTP 401.
- [ ] Confirm API-key comparisons use constant-time comparison.
- [ ] Keep API secrets exclusively in server-side environment variables.
- [ ] Do not place private credentials in VITE_* variables or frontend bundles.
- [ ] Document separate hosting requirements for the static Pages frontend and FastAPI backend.
- [ ] Require HTTPS for any remotely reachable API deployment.
- [ ] Restrict production CORS origins to the exact deployed frontend origin.
- [ ] Restrict trusted hosts to the actual API hostnames.
- [ ] Disable interactive API documentation in production deployments.
- [ ] Set explicit request-body size limits for event ingestion.
- [ ] Validate event field lengths before persistence.
- [ ] Reject unexpected event fields where strict validation is appropriate.
- [ ] Add per-client rate limits to write endpoints.
- [ ] Return a consistent 429 response when a rate limit is exceeded.
- [ ] Add tests for missing, incorrect, and valid API-key cases.
- [ ] Add tests for oversized event payloads.
- [ ] Add tests for malformed event payloads.
- [ ] Add tests for CORS preflight behavior.
- [ ] Add tests for disallowed Host headers.
- [ ] Ensure sensor ingestion sends its credential through a protected server-side configuration.
- [ ] Never print the sensor API key to stdout or log files.
- [ ] Use bounded network timeouts for sensor-to-API requests.
- [ ] Retry transient sensor failures with capped exponential backoff.
- [ ] Avoid retrying permanent authentication failures indefinitely.
- [ ] Persist sensor checkpoints atomically to avoid corrupt state after interruption.
- [ ] Restrict Windows event collection to the documented event IDs.
