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

- SOC dashboard: overview, alerts, authentication events, and detection rules
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

It establishes a first-run baseline, skips older records, and omits events with unusable account/IP fields. Its checkpoint `scripts/.sentinelforge_sensor_state.json` is generated locally and must not be committed. Polling is capped at 250 records per cycle.

## API reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health |
| GET | `/events?limit=100` | Events (limit 1–1000) |
| GET | `/alerts?limit=100&severity=medium` | Alerts with optional severity filter |
| POST | `/events` | Ingest validated event; requires `X-API-Key` |
| POST | `/demo/run` | Generate synthetic events; requires `X-API-Key` |

Write endpoints require `SENTINELFORGE_API_KEY`. If it is not configured, ingestion fails closed with HTTP 503. Configure exact origins and hostnames for deployments; see [Security Risk Register](docs/security-risk-register.md).

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

GitHub Actions runs backend tests/compile checks and frontend production build. A separate workflow audits dependencies.

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

Read-only endpoints (`GET /health`, `GET /events`, `GET /alerts`) do not require the key. If the API key is missing, write operations fail closed; a wrong key returns `401`.

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
