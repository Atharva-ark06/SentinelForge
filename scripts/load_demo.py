"""Load deterministic, synthetic authentication events into a running local API."""
from datetime import datetime, timedelta, timezone
import json
import os
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

BASE = os.environ.get("SENTINELFORGE_EVENTS_URL", "http://127.0.0.1:8000/events")
API_KEY = os.environ.get("SENTINELFORGE_API_KEY", "").strip()
if not API_KEY:
    raise SystemExit("Set SENTINELFORGE_API_KEY to the same secret configured on the API before loading demo events.")
start = datetime.now(timezone.utc) - timedelta(minutes=8)
events = []
for i in range(5):
    events.append({"timestamp": (start + timedelta(minutes=i)).isoformat().replace("+00:00", "Z"),
        "event_type": "login_failure", "username": "demo-admin", "source_ip": "192.0.2.10", "host": "lab-win01"})
for i, user in enumerate(["alice", "bob", "charlie"]):
    events.append({"timestamp": (start + timedelta(minutes=5+i)).isoformat().replace("+00:00", "Z"),
        "event_type": "login_failure", "username": user, "source_ip": "198.51.100.25", "host": "lab-linux01"})
for event in events:
    req = Request(BASE, data=json.dumps(event).encode(),
        headers={"Content-Type": "application/json", "X-API-Key": API_KEY}, method="POST")
    try:
        with urlopen(req, timeout=5) as response:
            result = json.loads(response.read())
            print(f"event={result['event_id']} new_alerts={result['new_alerts']} {event['username']} {event['event_type']}")
    except HTTPError as exc:
        raise SystemExit(f"API rejected request (HTTP {exc.code}). Verify key and server configuration.")
    except URLError as exc:
        raise SystemExit(f"Could not reach {BASE}. Start the API first. Details: {exc}")
