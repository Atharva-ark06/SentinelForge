# SentinelForge Architecture

## Components

1. **Event producers:** synthetic demo loader, API clients, or the optional read-only Windows sensor.
2. **Ingestion boundary:** FastAPI accepts `POST /events`; Pydantic validates timezone-aware timestamps, event types, account/host strings, and IPv4/IPv6 source addresses. Unknown fields are rejected.
3. **Detection engine:** evaluates a new event against persisted events from the same source IP in the preceding ten minutes.
4. **Persistence:** SQLite stores normalized events and alert candidates. Alert fingerprints prevent exact duplicate inserts.
5. **Query API:** `/health`, `/events`, and `/alerts` expose local lab data.

## Windows sensor flow

The sensor queries Windows Security Event IDs 4624 and 4625 via PowerShell, parses event XML, and compares event record IDs against a local checkpoint. On first run it records the newest visible record ID as a baseline rather than ingesting historical activity. Subsequent polls forward eligible events to the API. Records with unusable account names or source IPs are logged and skipped; no IP is fabricated. A failed API request leaves the checkpoint before that record so the event can be retried.

The sensor requires permission to read the Windows Security log and should be launched from an elevated PowerShell session. It does not change audit policy or block logons.

## Detection rules

- `SF-AUTH-001`: at least five failed logins for the same username and source IP within a ten-minute lookback.
- `SF-AUTH-002`: at least three distinct usernames associated with one source IP within a ten-minute lookback.

## Trust boundaries and limitations

- The API is unauthenticated and intended for localhost-only educational use.
- SQLite is suitable for a single-user prototype, not a distributed event index.
- Detection is heuristic and can produce false positives with NAT, proxies, test accounts, and administrative activity.
- The sensor queries up to 250 matching events per poll and is not a production endpoint agent.
- The detection window is backward-looking; late-arriving events and evolving evidence windows need more robust correlation and deduplication.
- No dashboard, authenticated enrollment, durable offline queue, alert lifecycle, or retention policy is implemented.
