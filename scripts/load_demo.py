"""Load deterministic, synthetic authentication events into a running local API."""
from datetime import datetime, timedelta, timezone
import json
from urllib.request import Request, urlopen
from urllib.error import URLError

BASE = "http://127.0.0.1:8000/events"
start = datetime(2026, 10, 28, 10, 0, tzinfo=timezone.utc)
events = []

# Synthetic repeated failures from a documentation-only IP range.
for i in range(5):
    events.append({
        "timestamp": (start + timedelta(minutes=i)).isoformat().replace("+00:00", "Z"),
        "event_type": "login_failure",
        "username": "demo-admin",
        "source_ip": "192.0.2.10",
        "host": "lab-win01",
    })

# Synthetic activity across several accounts from another documentation-only IP.
for i, user in enumerate(["alice", "bob", "charlie"]):
    events.append({
        "timestamp": (start + timedelta(minutes=20+i)).isoformat().replace("+00:00", "Z"),
        "event_type": "login_failure",
        "username": user,
        "source_ip": "198.51.100.25",
        "host": "lab-linux01",
    })

for event in events:
    req = Request(BASE, data=json.dumps(event).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=5) as response:
            result = json.loads(response.read())
            print(f"event={result['event_id']} new_alerts={result['new_alerts']} {event['username']} {event['event_type']}")
    except URLError as exc:
        raise SystemExit(f"Could not reach {BASE}. Start the API first. Details: {exc}")
