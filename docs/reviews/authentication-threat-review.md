# Authentication and API threat review

## Existing boundary

SentinelForge uses a shared `X-API-Key` for write operations. This is machine-to-machine authentication, **not user authentication**. A caller-supplied analyst label does not establish identity. There is no JWT session lifecycle, per-user RBAC, or MFA.

## Priority risks and mitigations

| Threat | Current consideration | Recommended verification |
| --- | --- | --- |
| Credential disclosure | API key must never be embedded in static Pages JavaScript | Scan built assets, examples, logs and workflows |
| Brute-force attempts | Per-process fixed-window limiter is insufficient across replicas | Edge limiter and tests for 401/429 responses |
| Cross-origin access | Explicit CORS allowlist | Test disallowed Origin and preflight |
| Host-header injection | TrustedHost middleware | Test unknown Host rejected |
| Telemetry exposure | Read endpoints can be public by default | Set protect-reads in private deployments |
| Timing attacks | Key comparison uses `hmac.compare_digest` | Regression test current/previous/invalid keys |
| Persistent XSS | Dashboard renders API-controlled fields | Ensure textContent or escaped React rendering; avoid innerHTML |
| Stale credentials | Current/previous key rotation | Define expiry and remove previous key after overlap |

## Backtracking / traceability

Record request ID, event ID, alert ID and audited alert status transitions. Never log API keys or sensitive event payloads. Trace an alert back to source events and a rule identifier. Check that malformed inputs cannot create incomplete audit records.

## Production limitation

Do not claim production-ready authentication until individual identities, role authorization, key expiry, distributed rate limiting, TLS termination, audit retention and deployment secret management are validated.
