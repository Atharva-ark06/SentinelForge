# SentinelForge

**A small, original defensive security monitoring lab built with FastAPI, SQLite, explainable detection rules, and an optional read-only Windows Security Event Log sensor.** It is inspired by common SIEM concepts and is not affiliated with, derived from, or a replacement for Wazuh.

## What works

- FastAPI event-ingestion API with strict Pydantic validation.
- SQLite persistence for normalized authentication events and alert evidence.
- Two explainable rules: repeated login failures and multiple accounts from one source.
- Query endpoints for health, events, and alerts.
- Synthetic demo data for repeatable demonstrations.
- Optional Windows sensor for Security Event IDs **4624** (successful logon) and **4625** (failed logon).
- Sensor checkpointing, retry-on-API-failure behavior, clear poll/skip/error output, and tests for event parsing and checkpoint files.

## Architecture

```text
Windows Security Log (optional)      Synthetic demo / API client
               |                                  |
               v                                  v
      Read-only Windows sensor --------------> FastAPI /events
                                                  |
                                           Pydantic validation
                                                  |
                                           Detection rules
                                                  |
                                           SQLite events/alerts
                                                  |
                                        /health /events /alerts
```

## Requirements

- Python 3.11 or newer recommended.
- Windows 10/11 for the Windows Event Log sensor.
- Elevated PowerShell is required to read the Windows **Security** log on typical Windows installations.

## Quick start — Windows PowerShell

From the project folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn sentinelforge.api:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API documentation. Keep the API terminal running.

In a second terminal, activate the same environment and load demo events:

```powershell
cd D:\SentinelForge
.\.venv\Scripts\Activate.ps1
python .\scripts\load_demo.py
```

Inspect results at `http://127.0.0.1:8000/health`, `http://127.0.0.1:8000/events`, and `http://127.0.0.1:8000/alerts`.

## Windows sensor (optional)

1. Start the API using the steps above.
2. Open **PowerShell as Administrator**. The sensor process itself must be elevated; elevating a separate diagnostic window is not enough.
3. Run:

```powershell
cd D:\SentinelForge
.\.venv\Scripts\Activate.ps1
python .\scripts\windows_sensor.py
```

Useful options:

```powershell
python .\scripts\windows_sensor.py --once
python .\scripts\windows_sensor.py --interval 5
python .\scripts\windows_sensor.py --api-url http://127.0.0.1:8000/events
```

On first run, the sensor stores a baseline record ID and deliberately does **not** ingest old log entries. On later polls it prints a status line even when there are no new events. It sends only events with a usable account, timestamp, host, and valid source IP. Many local Windows logons (including service logons) report `IpAddress` as `-`; those are logged as `[SKIP]` and are not assigned a fabricated IP. This means a single Windows workstation may produce no sensor-ingested events during ordinary local use. Use the synthetic demo path to demonstrate detection rules reliably.

The sensor reads logs only. It does not change audit policy, block logons, or perform remediation. It queries up to 250 matching events per poll, so extremely high event volume could exceed this prototype's collection limit. It uses a local checkpoint file at `scripts/.sentinelforge_sensor_state.json`; do not commit that generated file.

## Detection rules

| Rule | Trigger | Severity | Interpretation |
|---|---|---|---|
| `SF-AUTH-001` | At least 5 failed logins for the same username and source IP in a 10-minute lookback | Medium | May indicate password guessing |
| `SF-AUTH-002` | At least 3 distinct usernames associated with one source IP in a 10-minute lookback | Medium | May indicate password spraying or account enumeration |

These are heuristics, not proof of compromise. NAT, proxies, test activity, and legitimate administration can produce false positives.

## Tests

```powershell
python -m pytest -q
```

The included test suite covers API validation, both detection rules, and Windows event parsing/checkpoint behavior. Run the suite in your environment before submission and report the result from that run.

## Security and scope limitations

- This is an educational, local-first prototype. The API has no authentication or authorization; keep it bound to localhost and do not expose it to an untrusted network.
- No dashboard, endpoint enrollment, authenticated agent tokens, durable offline queue, alert triage workflow, retention policy, or distributed storage is included.
- The Windows sensor has a simple polling/checkpoint design and a 250-event query limit. It is not a production endpoint agent.
- Before any non-local deployment, add authentication/authorization, TLS, rate limiting, secrets management, retention controls, monitoring, and a threat-model review.
- Use synthetic or authorized lab data only. `192.0.2.0/24` and `198.51.100.0/24` are documentation-only IPv4 ranges.

## Project structure

```text
sentinelforge/        API, schema, database, detection rules
scripts/load_demo.py  Repeatable synthetic event generator
scripts/windows_sensor.py  Optional Windows Security log sensor
tests/                API and sensor tests
docs/                 Architecture and roadmap
```

## Roadmap

See [`docs/roadmap.md`](docs/roadmap.md) for completed work and future hardening tasks. The current deliverable is an educational prototype, not a production SIEM.
