# SentinelForge

**Local-first defensive security monitoring prototype** using FastAPI, SQLite, explainable authentication detections, an optional read-only Windows Security Event Log sensor, and a React SOC dashboard.

> Educational project—not a production SIEM. Use synthetic or explicitly authorized lab telemetry only.

## Dashboard preview

| Overview | Alerts |
|---|---|
| ![Overview dashboard](https://res.cloudinary.com/wpop4xyo/image/upload/v1793213099/overview_of_dashboard.png) | ![Alerts](https://res.cloudinary.com/wpop4xyo/image/upload/v1793213000/alerts.png) |

| Authentication events | Detection rules |
|---|---|
| ![Events](https://res.cloudinary.com/wpop4xyo/image/upload/v1793213058/authentication_events.png) | ![Rules](https://res.cloudinary.com/wpop4xyo/image/upload/v1793213025/detections_rules.png) |

## Capabilities

- SOC dashboard: overview, alerts, authentication events, detection rules, and database-wide metrics
- Alert investigation lifecycle with audited status transitions and analyst notes
- Filtered, offset-paginated event and alert APIs
- FastAPI REST API with validated event ingestion and health endpoint
- SQLite persistence for normalized event records and alert evidence
- Explainable rules for repeated authentication failures and multi-account source activity
- Synthetic demo event generator for repeatable walkthroughs
- Optional read-only Windows sensor for Security Event IDs 4624 and 4625
- Python tests, React/TypeScript frontend, CI, dependency audit, and GitHub Pages workflow

## Stack

**Backend:** Python · FastAPI · Pydantic · Uvicorn  
**Storage:** SQLite  
**Frontend:** React · TypeScript · Vite · Tailwind CSS · Recharts · Lucide  
**Sensor:** Python Windows Event Log reader

## Architecture

```text
Windows Security Event Log (optional)       Synthetic demo / API client
                   |                                    |
                   v                                    v
          Read-only sensor ------------------------> FastAPI
                                                       |
                                                Pydantic validation
                                                       |
                                                Detection rules
                                                       |
                                                  SQLite
                                                       |
                                             React SOC dashboard
```

## Run locally (Windows PowerShell)

### Backend

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn sentinelforge.api:app --reload
```

API: `http://127.0.0.1:8000` · Swagger: `http://127.0.0.1:8000/docs`

### Frontend (second terminal)

```powershell
cd frontend
npm install
npm run dev
```

Vite normally serves `http://127.0.0.1:5173` and proxies API routes to the local FastAPI process. For a remote Pages deployment, configure the separate API and `VITE_API_BASE_URL` as described in [Deployment](docs/deployment.md).

### Synthetic demo

```powershell
# From repository root, with backend running
python .\scripts\load_demo.py
```

## Detection rules

| Rule | Threshold | Meaning |
|---|---|---|
| `SF-AUTH-001` | ≥5 failed logins for one username + source IP in 10 minutes | Possible password guessing |
| `SF-AUTH-002` | ≥3 distinct usernames associated with one source IP in 10 minutes | Possible password spraying / enumeration |

These heuristics can produce false positives (NAT, proxies, admin activity, lab tests). Alerts are not proof of compromise.

## Optional Windows sensor

The sensor reads Security Event IDs **4624** (successful logon) and **4625** (failed logon). It does not change audit policy, block logons, or remediate.

```powershell
# Run from repository root; elevated PowerShell may be required
.\.venv\Scripts\Activate.ps1
$env:SENTINELFORGE_API_KEY = "your_configured_api_key"
python .\scripts\windows_sensor.py
python .\scripts\windows_sensor.py --once
python .\scripts\windows_sensor.py --interval 5
```

It establishes a first-run baseline from the newest records, then reads subsequent records after its checkpoint in oldest-first batches so a burst larger than one poll does not silently skip the backlog. Remote API URLs must use HTTPS; plain HTTP is accepted only for localhost/loopback. It omits events with unusable account/IP fields. Its checkpoint `scripts/.sentinelforge_sensor_state.json` is generated locally and must not be committed. Polling defaults to 250 records per cycle and can be tuned with `--max-events` (maximum 10,000).

## API reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health |
| GET | `/events?limit=100&offset=0` | Filtered/paginated events (type, username, source IP, time range) |
| GET | `/metrics` | Database-wide event and alert totals, severity and status counts |
| GET | `/alerts?limit=100&offset=0&severity=medium&status=new` | Filtered/paginated alerts |
| GET | `/alerts/{id}/activity` | Alert status transition history |
| PATCH | `/alerts/{id}/status` | Change alert status; requires `X-API-Key` |
| POST | `/events` | Ingest validated event; requires `X-API-Key` |
| POST | `/demo/run` | Generate synthetic events; requires `X-API-Key` |

Write endpoints and alert status changes require `SENTINELFORGE_API_KEY`. If it is not configured, protected operations fail closed with HTTP 503. Set `SENTINELFORGE_PROTECT_READS=true` on the API process to require this key for telemetry reads too (recommended for private deployments). Configure exact origins and hostnames for deployments; see [Security Risk Register](docs/security-risk-register.md).

## Alert investigation workflow

Alerts begin in `new`. Analysts can move them through `acknowledged`, `investigating`, `resolved`, and `false_positive` using the authenticated API or CLI. Every successful transition is stored in `alert_activity`. Existing SQLite databases are upgraded additively at startup; back up production data before deploying schema changes.

Set `SENTINELFORGE_API_KEY` and run:

```powershell
python .\scripts\manage_alert.py --alert-id 1 --status acknowledged --actor "analyst-id" --note "Initial triage"
```

See [lifecycle overview](docs/alerts/lifecycle-overview.md), [allowed transitions](docs/alerts/status-transitions.md), [audit history](docs/alerts/audit-history.md), and [CLI guide](docs/development/alert-workflow-cli.md).

**Attribution limitation:** `actor` is a caller-supplied label protected by the shared machine key; it is not a verified user identity. The API still has unauthenticated read endpoints. Use synthetic data only on public deployments until user authentication and read authorization are implemented.

## Tests and build

```powershell
# Repository root
python -m pytest -q
python -m compileall -q sentinelforge scripts

# Frontend
cd frontend
npm ci
npm run build
```

GitHub Actions tests Python 3.11–3.13, compiles backend modules, type-checks/builds the frontend, and audits Python plus frontend production and development dependencies. GitHub Pages builds from a generated npm lockfile before installing with `npm ci`.

## Configure your own API key (local backend)

SentinelForge protects its write endpoints with a shared API key. **Generate your own key; never use a key published in screenshots, commits, chat, or examples.** The key is for your local/deployed API—not GitHub Pages. Keep it private and rotate it if exposed.

### 1. Generate a strong key (PowerShell)

From the repository root:

```powershell
$env:SENTINELFORGE_API_KEY = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:SENTINELFORGE_API_KEY
```

Copy the generated value into your local `.env` file (do not commit it).

### 2. Create a local `.env`

Create `.env` in the repository root:

```dotenv
SENTINELFORGE_API_KEY=replace_with_your_generated_secret
SENTINELFORGE_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
SENTINELFORGE_ALLOWED_HOSTS=127.0.0.1,localhost,testserver
SENTINELFORGE_ENABLE_DOCS=true
# Optional: store the SQLite database at a custom path
# SENTINELFORGE_DB=sentinelforge.sqlite3
```

The repository's `.gitignore` excludes `.env`. Verify before committing:

```powershell
git check-ignore .env
git status --short
```

### 3. Load `.env` when starting the API

FastAPI does **not** automatically read `.env`. Install Uvicorn's dotenv support if needed, then start the server with `--env-file`:

```powershell
python -m pip install "uvicorn[standard]" python-dotenv
python -m uvicorn sentinelforge.api:app --reload --env-file .env
```

Alternatively, set the environment variable directly in the current PowerShell session before launching Uvicorn:

```powershell
$env:SENTINELFORGE_API_KEY = "paste_your_generated_key_here"
python -m uvicorn sentinelforge.api:app --reload
```

### 4. Send the key with write requests

Use the `X-API-Key` header for `POST /events` and `POST /demo/run`. Example with PowerShell:

```powershell
$headers = @{ "X-API-Key" = $env:SENTINELFORGE_API_KEY }
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/demo/run" -Headers $headers
```

By default read-only endpoints do not require the key. When `SENTINELFORGE_PROTECT_READS=true`, telemetry reads (`GET /events`, `GET /alerts`, `GET /metrics`, and alert activity) require `X-API-Key`; `GET /health` remains public. If the API key is missing, protected operations fail closed; a wrong key returns `401`. The public demo frontend does not provide an authenticated read session; use synthetic data there.

**Never** put secrets in frontend source code, `VITE_*` variables, GitHub Pages, screenshots, or committed files. GitHub Pages serves only static frontend assets and cannot securely hold a private API key. For a remotely hosted API, use the host's secret/environment-variable settings, HTTPS, and exact production origin/host allowlists; do not expose the API directly to the public internet without additional controls.

## GitHub Pages

The `.github/workflows/pages.yml` workflow builds and deploys the **static React frontend** from `main`. Pages does not host FastAPI, SQLite, or the Windows sensor. Live API functionality requires a separately deployed API over HTTPS with secure configuration. Set the repository Actions variable `VITE_API_BASE_URL` to the public API origin (for example `https://api.example.com`, without a trailing slash); the value is public and must never contain a secret. Configure the API CORS origin and allowed host values on the backend host. See [Deployment](docs/deployment.md) for the complete setup and troubleshooting steps.

After merge, select **Settings → Pages → Build and deployment → GitHub Actions**.

Project site: **https://atharva-ark06.github.io/SentinelForge/**

## Documentation hub

- [Architecture overview](docs/architecture/overview.md)
- [Deployment and dashboard troubleshooting](docs/deployment.md)
- [Production readiness checklist](docs/operations/production-readiness.md)
- [Incident response workflow](docs/operations/incident-response.md)
- [Detection rule guides](docs/detections/)
- [Analyst playbooks](docs/playbooks/)
- [Security and privacy guidance](docs/security/)
- [Testing strategy](docs/testing/test-strategy.md)
- [Contribution and release checklists](docs/development/)

## Security and risk management

The [risk register](docs/security-risk-register.md) documents likelihood × impact scoring, controls, treatment, residual risk, and a deployment gate mapped for learning to:

- NIST Cybersecurity Framework (CSF) 2.0
- NIST SP 800-30 Rev. 1 (risk assessment)
- NIST SP 800-53 Rev. 5 (security/privacy controls)
- NIST SP 800-218 (Secure Software Development Framework)
- ISO/IEC 27001:2022 (ISMS)
- OWASP ASVS (application security verification)

This is a practical alignment—not an audit, certification, or compliance attestation.

## Repository layout

```text
sentinelforge/                 API, models, database, detection logic
scripts/load_demo.py           Synthetic event generator
scripts/windows_sensor.py       Optional Windows event sensor
tests/                         Backend and sensor tests
docs/                         Architecture, roadmap, risk register
frontend/                      React SOC dashboard
.github/workflows/              CI, dependency audit, Pages deploy
```

## Limitations and responsible use

- Prototype scope: local-first, rule-based, single-node SQLite.
- Do not expose the API directly to untrusted networks.
- Do not upload real user or organizational telemetry without authorization and security review.
- Production readiness requires robust identity/authorization, rate limiting, TLS, secrets management, retention, backups, monitoring, incident response, and independent threat modeling.


## Sensor transport and backlog safety

The Windows sensor sends the shared ingestion key in the `X-API-Key` header. Use HTTPS for any non-loopback API host; plain HTTP is intentionally restricted to `localhost` and loopback addresses for local development. Do not pass secrets on command lines where process listings may expose them; prefer the `SENTINELFORGE_API_KEY` environment variable.

The first sensor poll establishes a baseline from the newest visible matching records and does not replay the historical log. Later polls query records with an event record ID greater than the saved checkpoint and read oldest-first in bounded batches. If the sensor falls behind, it drains the backlog over successive polls rather than skipping records merely because more than one batch accumulated. Checkpoint files are local operational state and must remain untracked.

See [Windows sensor security and operations](docs/security/windows-sensor.md) for the transport policy, checkpoint behavior, limitations and recovery guidance.


## Secure Docker quick start

1. Copy `.env.example` to `.env` and generate a unique `SENTINELFORGE_API_KEY`.
2. Run `docker compose up --build` from the repository root.
3. Check `http://127.0.0.1:8000/health`. The container binds to loopback, runs as a non-root user, and persists SQLite in a named volume.
4. Read `CONTRIBUTING.md` before submitting changes. See `LICENSE` for reuse terms.

**Request limiting:** The API applies an in-process fixed-window rate limit (600 reads/minute and 120 writes/minute per client IP by default). Configure `SENTINELFORGE_READ_RATE_LIMIT` and `SENTINELFORGE_WRITE_RATE_LIMIT` for a single-worker lab. This is not a distributed or proxy-aware limiter; place a trusted gateway in front of any internet-facing deployment and do not trust client-supplied forwarding headers.

**Quality checks:** Run `python -m pytest -q`, `python -m compileall -q sentinelforge scripts`, and `ruff check sentinelforge/rate_limit.py tests/test_rate_limit.py tests/test_ip_validation_regression.py`. The focused lint workflow covers the newly introduced security modules; existing legacy code still needs a separate formatting pass.

**Architecture diagram:** See [data flow](docs/architecture/overview.md). Never put API keys in Vite variables or browser bundles.


## PR #32 dashboard, API integration, and security updates

The React GitHub Pages dashboard has a top-right light/dark theme switcher and
accessible, responsive metric cards. **Preview synthetic data** displays clearly
labelled fictional records in browser memory without submitting anything to the
backend. The preview uses documentation-only IP addresses and is not evidence
of an incident, API connectivity, or a live data feed. Exit preview to resume
live API reads. Preview mode disables live refresh actions and marks its metrics,
chart, tables, and connection indicators as synthetic.

### Connecting the live dashboard

1. Deploy FastAPI and SQLite separately; GitHub Pages serves static frontend
   files only. Set `VITE_API_BASE_URL` to the reachable HTTPS API origin in
   the GitHub Actions build environment, then redeploy Pages.
2. On the API host, set `SENTINELFORGE_ALLOWED_ORIGINS` to the exact Pages
   origin and `SENTINELFORGE_ALLOWED_HOSTS` to the API host. Never put API
   keys in `VITE_*` values or in browser JavaScript.
3. Open the deployed dashboard and check the API status. Live mode requests
   `/health`, `/events?limit=250`, `/alerts?limit=250`, and `/metrics`.
   Errors, invalid JSON responses, and request timeouts are reported rather
   than silently rendered as an empty dashboard.
4. For authorized local demonstration data, set the backend API key and run
   `python scripts/load_demo.py` from the repository root. Browser preview
   never modifies the database. Do not expose real security telemetry to
   unauthenticated internet clients; set `SENTINELFORGE_PROTECT_READS=true`
   behind a trusted authentication gateway for sensitive environments.

### Hardening and validation

API write operations require a configured secret and compare keys with
`hmac.compare_digest`; oversized key headers are rejected. Read protection
is optional and must be explicitly enabled. CORS uses an allowlist and is
**not** an authentication mechanism. The API adds defensive response headers,
query-value validation, and bounded rate limiting. The expanded regression
suite covers authentication, malformed filters, and HTTP response headers.

Review [the production hardening checklist](docs/reviews/production-hardening-checklist.md),
[authentication threat review](docs/reviews/authentication-threat-review.md),
and [live-data audit](docs/reviews/dashboard-live-data-audit.md).

**Validation status:** A commit count is not a substitute for passing tests.
Run the complete backend tests, frontend TypeScript build, dependency audit,
and GitHub Actions checks before merging. This README does not claim those
checks have passed.
