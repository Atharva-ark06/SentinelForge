# Security baseline and risk register

SentinelForge is an educational, local-first monitoring prototype. This mapping draws on NIST CSF 2.0, NIST SP 800-30 Rev. 1, NIST SP 800-53 Rev. 5, NIST SP 800-218 (SSDF), ISO/IEC 27001:2022 and OWASP ASVS. It is not a certification or compliance claim.

## Risk methodology

Use a 1–5 likelihood × 1–5 impact matrix. Scores: 1–4 Low, 5–9 Moderate, 10–16 High, 17–25 Critical. Reassess after architecture, exposure, data, or dependency changes; record owner, treatment, evidence, and residual risk.

| ID | Risk | L | I | Score | Treatment | Residual |
|---|---|---:|---:|---:|---|---|
| SF-R01 | Unauthenticated event injection / demo abuse | 4 | 4 | 16 High | API key on write routes; constant-time compare; fail closed when absent | Moderate |
| SF-R02 | API exposed to untrusted networks | 4 | 5 | 20 Critical | Trusted Host allowlist, restrictive CORS, localhost binding, TLS reverse proxy | High until architecture reviewed |
| SF-R03 | Clickjacking / content injection | 3 | 4 | 12 High | CSP frame-ancestors, X-Frame-Options, nosniff, no-store | Low–Moderate |
| SF-R04 | Payload/resource exhaustion | 3 | 4 | 12 High | Pydantic strict fields, bounded values and query limits; edge rate limit needed | Moderate |
| SF-R05 | Telemetry disclosure | 3 | 5 | 15 High | Local SQLite, data minimization, retention/access controls required | Moderate |
| SF-R06 | Vulnerable dependencies | 3 | 5 | 15 High | CI pip/npm audit and Dependabot | Moderate |
| SF-R07 | CI supply-chain compromise | 3 | 5 | 15 High | Least-privilege permissions; pin Actions by SHA; protect main/review | Moderate |
| SF-R08 | False positives / evasion | 4 | 3 | 12 High | Explainable rules, evidence, tuning, authorized test data | Moderate |
| SF-R09 | Sensor over-collection / privileges | 3 | 4 | 12 High | Read-only event access, opt-in, minimum privileges; no audit-policy changes | Low–Moderate |
| SF-R10 | Static demo mistaken for live SOC | 3 | 3 | 9 Moderate | Label demo/static mode; never publish real logs or secrets | Low |

## Controls implemented

- `SENTINELFORGE_API_KEY` protects `POST /events` and `POST /demo/run`; unset means 503 (ingestion disabled).
- API key comparison uses `hmac.compare_digest`; use HTTPS outside localhost.
- `SENTINELFORGE_ALLOWED_ORIGINS` restricts CORS to exact origins; credentials are disabled.
- `SENTINELFORGE_ALLOWED_HOSTS` configures TrustedHost validation.
- Response headers include CSP, frame denial, nosniff, Referrer-Policy, Permissions-Policy and no-store.
- Set `SENTINELFORGE_ENABLE_DOCS=false` to disable Swagger in deployment.
- CI includes tests, compile checks, frontend build, dependency audit; Dependabot monitors ecosystems.

## Configuration

| Variable | Purpose |
|---|---|
| `SENTINELFORGE_API_KEY` | Required write-route secret |
| `SENTINELFORGE_ALLOWED_ORIGINS` | Comma-separated exact browser origins |
| `SENTINELFORGE_ALLOWED_HOSTS` | Comma-separated hostnames for API deployment |
| `SENTINELFORGE_ENABLE_DOCS` | Swagger toggle (default true for local learning) |
| `SENTINELFORGE_DB` | SQLite path |

## NIST CSF 2.0 deployment gate

1. **Govern:** scope, owner, data classification, risk acceptance, incident contacts.
2. **Identify:** inventory data flows, dependencies, hosts, and threats; reassess risk.
3. **Protect:** HTTPS, secrets manager, exact CORS/Host allowlists, network restrictions, encrypted backups.
4. **Detect:** centralized logs, dependency alerts, monitor errors and authentication failures.
5. **Respond:** triage, containment, evidence preservation, communication, tabletop exercise.
6. **Recover:** tested restore, retention, key rotation, recovery objectives.
7. **Verify:** code review, threat modeling, authorized security testing before production telemetry.

## References

- NIST CSF 2.0: https://www.nist.gov/cyberframework
- NIST SP 800-30 Rev. 1: https://csrc.nist.gov/pubs/sp/800/30/r1/final
- NIST SP 800-53 Rev. 5: https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final
- NIST SP 800-218 SSDF: https://csrc.nist.gov/pubs/sp/800/218/final
- ISO/IEC 27001:2022: https://www.iso.org/standard/27001
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/
