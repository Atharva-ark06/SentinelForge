# SentinelForge

**A local-first defensive security monitoring prototype** built with FastAPI, SQLite, explainable authentication detection rules, an optional read-only Windows Security Event Log sensor, and a React SOC dashboard.

SentinelForge demonstrates a basic security monitoring workflow: collect authentication events, evaluate detection rules, store alert evidence, and review results in a dashboard. It is an educational prototype, not a production SIEM.

Based on Task 6 and 13 combined (EduRankAI)

## Dashboard Preview

The screenshots below are loaded directly from Cloudinary.

### 1. Overview Dashboard
![SentinelForge Overview Dashboard](https://res.cloudinary.com/wpop4xyo/image/upload/v1793213099/overview_of_dashboard.png)

### 2. Alerts
![SentinelForge Alerts](https://res.cloudinary.com/wpop4xyo/image/upload/v1793213000/alerts.png)

### 3. Authentication Events
![SentinelForge Authentication Events](https://res.cloudinary.com/wpop4xyo/image/upload/v1793213058/authentication_events.png)

### 4. Detection Rules
![SentinelForge Detection Rules](https://res.cloudinary.com/wpop4xyo/image/upload/v1793213025/detections_rules.png)

## Features

- **SOC dashboard:** Overview, Alerts, Events, and Detection Rules views.
- **FastAPI backend:** API endpoints for health status, events, alerts, and demo data.
- **SQLite storage:** Persists normalized authentication events and alert evidence.
- **Explainable detection:** Two rule-based detections for suspicious authentication patterns.
- **Synthetic demo mode:** Generates repeatable sample events for demonstrations.
- **Optional Windows sensor:** Reads Windows Security Event IDs **4624** (successful logon) and **4625** (failed logon) in read-only mode.
- **Input validation and tests:** Pydantic request validation and tests for API behavior, detection rules, and sensor parsing/checkpoint behavior.

## Technology Stack

- **Backend:** Python, FastAPI, Uvicorn, Pydantic
- **Database:** SQLite
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Visualization and icons:** Recharts, Lucide
- **Sensor:** Python with Windows Security Event Log access

## Architecture

```text
Windows Security Log (optional)       Synthetic demo / API client
                |                                  |
                v                                  v
       Read-only Windows sensor --------------> FastAPI API
                                                   |
                                            Pydantic validation
                                                   |
                                             Detection rules
                                                   |
                                            SQLite events/alerts
                                                   |
                                     React SOC dashboard (Vite)
                                     Overview / Alerts / Events / Rules
```

## Quick Start — Windows PowerShell

### 1. Set up the Python environment

From the repository root:

```powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Start the backend

Keep this terminal open:

```powershell
python -m uvicorn sentinelforge.api:app --reload
```

The API runs at `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 3. Start the frontend

Open a second terminal in the repository root:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite (normally `http://127.0.0.1:5173`). The Vite development server proxies `/health`, `/events`, `/alerts`, and `/demo/run` to the FastAPI backend on port 8000. Keep both backend and frontend running while using the dashboard.

### 4. Load demo events

With the backend running, use the dashboard's **Run demo** action or run the script from a third terminal at the repository root:

```powershell
python .\\scripts\\load_demo.py
```

Inspect the API directly at:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/events`
- `http://127.0.0.1:8000/alerts`

## Detection Rules

| Rule | Trigger | Severity | Interpretation |
|---|---|---|---|
| `SF-AUTH-001` | At least 5 failed logins for the same username and source IP within a 10-minute lookback | Medium | May indicate password guessing |
| `SF-AUTH-002` | At least 3 distinct usernames associated with one source IP within a 10-minute lookback | Medium | May indicate password spraying or account enumeration |

These rules are heuristics, not proof of compromise. NAT, proxies, legitimate administration, and test activity can cause false positives. The rule cards in the frontend describe the current backend rules; the backend does not currently expose a dedicated rules API endpoint.

## Optional Windows Security Event Log Sensor

The sensor reads Windows Security Event IDs 4624 and 4625 and forwards eligible events to the API. It does not change audit policy, block logons, or perform remediation.

1. Start the backend first.
2. Open **PowerShell as Administrator**; typical Windows installations require elevated permissions to read the Security log.
3. From the repository root, activate the virtual environment and run:

```powershell
.\\.venv\\Scripts\\Activate.ps1
python .\\scripts\\windows_sensor.py
```

Useful options:

```powershell
python .\\scripts\\windows_sensor.py --once
python .\\scripts\\windows_sensor.py --interval 5
python .\\scripts\\windows_sensor.py --api-url http://127.0.0.1:8000/events
```

On first run, the sensor saves a baseline record ID and deliberately does not ingest older log entries. It only sends events with a usable account, timestamp, host, and valid source IP. Many local Windows logons report the IP address as `-`, so they are skipped rather than assigned a fabricated IP. A single workstation may therefore produce no sensor-ingested events during ordinary local use; the synthetic demo path is available for repeatable demonstrations.

The sensor uses a local checkpoint file at `scripts/.sentinelforge_sensor_state.json`; do not commit this generated file. It queries up to 250 matching events per poll, so high event volume can exceed this prototype's collection limit.

## Tests and Build

Run the backend tests from the repository root:

```powershell
python -m pytest -q
```

Build the frontend from the repository root:

```powershell
cd frontend
npm install
npm run build
```

Run these commands in your environment before submission and report the actual results. A successful local app launch alone does not establish that every test or production build has passed.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | API health check |
| `GET` | `/events` | Retrieve stored security events |
| `GET` | `/alerts` | Retrieve generated alerts |
| `POST` | `/demo/run` | Insert synthetic demo events |

The frontend uses the existing FastAPI backend; no external AI or threat-intelligence API is required.

## Security and Scope Limitations

- This is an educational, local-first prototype. The API does not implement authentication or authorization; keep it bound to localhost and do not expose it to an untrusted network.
- The Windows sensor is a simple polling/checkpoint design, not a production endpoint agent.
- Synthetic demo events use documentation-only IPv4 ranges such as `192.0.2.0/24` and `198.51.100.0/24`; they are not real source telemetry.
- Production use would require authentication/authorization, TLS, rate limiting, secrets management, retention controls, monitoring, resilient ingestion, and a threat-model review.
- Use synthetic or otherwise authorized lab data only.

## Project Structure

```text
sentinelforge/                  API, schema, database, detection rules
scripts/load_demo.py            Repeatable synthetic event generator
scripts/windows_sensor.py       Optional Windows Security log sensor
tests/                          API and sensor tests
docs/                            Architecture and roadmap
frontend/                       React SOC dashboard
```

## Roadmap

See [`docs/roadmap.md`](docs/roadmap.md) for completed work and future hardening tasks. SentinelForge is a learning and demonstration prototype, not a production SIEM.
