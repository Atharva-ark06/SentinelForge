# SentinelForge Roadmap

## Completed in this prototype
- [x] Validated FastAPI event ingestion and timezone-aware timestamps.
- [x] SQLite event/alert persistence.
- [x] Explainable authentication rules SF-AUTH-001 and SF-AUTH-002.
- [x] Health, event, and alert endpoints.
- [x] Synthetic demo-event loader.
- [x] Windows Security Event Log sensor for Event IDs 4624 and 4625.
- [x] First-run baseline, checkpoint persistence, API error handling, and visible polling status.
- [x] Automated API and sensor parsing/checkpoint tests.

## Known limitations
- Sensor only forwards events with a valid source IP; local events without an IP are skipped.
- Sensor polls at most 250 matching records per cycle; high-volume environments can lose coverage between polls.
- A local checkpoint is not a durable queue; skipped events are intentionally checkpointed, and an API failure retries the failed event on the next poll.
- Detection uses a backward-looking 10-minute window and simple evidence fingerprints.
- No authentication, authorization, dashboard, endpoint enrollment, alert status workflow, retention policy, or production deployment configuration.

## Future work
1. Add sensor integration tests using a mocked PowerShell subprocess and mocked HTTP endpoint.
2. Add a durable retry queue, endpoint heartbeat, and event-volume/lag metrics.
3. Add alert lifecycle management and query filters.
4. Add dashboard and analyst investigation timeline.
5. Add API authentication, TLS guidance, rate limiting, retention controls, CI, and threat-model/security tests.
