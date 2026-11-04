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

Vite normally serves `http://127.0.0.1:5173` and proxies API routes to the local FastAPI process.

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

## GitHub Pages

The `.github/workflows/pages.yml` workflow builds and deploys the **static React frontend** from `main`. Pages does not host FastAPI, SQLite, or the Windows sensor. Live API functionality requires a separately deployed API over HTTPS with secure configuration.

After merge, select **Settings → Pages → Build and deployment → GitHub Actions**.

Project site: **https://atharva-ark06.github.io/SentinelForge/**

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
