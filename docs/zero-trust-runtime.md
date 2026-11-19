# Zero-trust runtime controls

## Content Security Policy

The FastAPI root dashboard receives a fresh, cryptographically random nonce on
each request. Its inline script and stylesheet carry that nonce. CSP denies all
other script and style sources; do not add inline event handlers or `unsafe-inline`.
The separately built React UI must configure equivalent CSP at its own hosting
origin; API response headers do not configure independently hosted pages.

## API key rotation

Configure `SENTINELFORGE_API_KEY_CURRENT` with a generated secret. During a
planned rotation, set `SENTINELFORGE_API_KEY_PREVIOUS` to the old value, deploy
the new CURRENT, update sensors, then **remove PREVIOUS** after a bounded
overlap window. `SENTINELFORGE_API_KEY` remains a legacy fallback. Secrets are
not JWTs: SentinelForge has no JWT login, refresh tokens, session table, or
password reset flow. Immediate credential revocation requires removing the
previous key and restarting all instances. Do not claim session-level revocation.

## SQLite limitations and schema migration

Routine database connections install a SQLite authorizer that rejects table
creation, alteration, drops, and attaching other databases. Startup migrations
use a separately flagged `schema_admin=True` connection. This is defense in
depth, **not a database principal or operating-system access boundary**: a
process with file-system write access can still change or delete SQLite files.
To provide true `SELECT/INSERT/UPDATE/DELETE`-only roles, migrate to a database
server (for example PostgreSQL), provision a migration owner separately from
the application role, and grant only table DML to the application account.

## Network egress

The default Compose network is `internal: true`, disabling external routed
egress from the API container. The API currently needs no outbound third-party
calls. If outbound integrations are introduced, route them through a controlled
egress proxy with an explicit destination allowlist and tests; do not simply
remove the isolation silently. Validate ingress and dashboard access after
deployment in the target Docker environment.

## PR gates

CI checks first-party Python import cycles, copy/paste duplicates in the
frontend (`jscpd`), and prohibited GPL/AGPL dependency licenses. Reviewdog
publishes Ruff findings on pull requests. These gates are a baseline and do not
replace dependency audit or security review. License decisions require human
review for ambiguous, dual-licensed, LGPL, or unknown packages.

## Branch governance

Repository rulesets and signature requirements must be configured by a GitHub
administrator under Settings → Rules → Rulesets. Require approving review,
passing CI/audit/lint/review checks, linear history, and signed commits. GitHub
App integrations cannot always administer repository rulesets. Do not enable
strict required checks until their names and successful runs are verified.
