from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

WINDOW = timedelta(minutes=10)
FAILURE_THRESHOLD = 5
MULTI_ACCOUNT_THRESHOLD = 3


def _parse_ts(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def evaluate_new_event(new_event_id: int, db_path=None) -> list[dict[str, Any]]:
    """Evaluate a newly inserted event against recent events and return explainable alerts."""
    from .db import connection

    with connection(db_path) as conn:
        current = conn.execute("SELECT * FROM events WHERE id=?", (new_event_id,)).fetchone()
        if current is None:
            return []
        current = dict(current)
        current_time = _parse_ts(current["timestamp"])
        start = (current_time - WINDOW).isoformat()
        end = current_time.isoformat()
        recent = conn.execute(
            """SELECT * FROM events WHERE timestamp >= ? AND timestamp <= ?
               AND source_ip = ? ORDER BY timestamp, id""",
            (start, end, current["source_ip"]),
        ).fetchall()
        recent = [dict(row) for row in recent]

    failures_for_user = [
        e for e in recent
        if e["event_type"] == "login_failure" and e["username"] == current["username"]
    ]
    alerts: list[dict[str, Any]] = []

    if len(failures_for_user) >= FAILURE_THRESHOLD:
        ids = [e["id"] for e in failures_for_user]
        fingerprint = sha256(
            f"SF-AUTH-001|{current['source_ip']}|{current['username']}|{ids[0]}|{ids[-1]}".encode()
        ).hexdigest()
        alerts.append({
            "rule_id": "SF-AUTH-001",
            "fingerprint": fingerprint,
            "title": "Repeated authentication failures",
            "severity": "medium",
            "description": (
                f"{len(failures_for_user)} failed logins for account "
                f"{current['username']!r} from {current['source_ip']} within 10 minutes. "
                "This may indicate password guessing; verify user activity and source ownership."
            ),
            "evidence": ids,
            "source_ip": current["source_ip"],
            "username": current["username"],
            "first_seen": failures_for_user[0]["timestamp"],
            "last_seen": failures_for_user[-1]["timestamp"],
        })

    distinct_users = sorted({e["username"] for e in recent})
    if len(distinct_users) >= MULTI_ACCOUNT_THRESHOLD:
        related = [e for e in recent if e["username"] in distinct_users]
        ids = [e["id"] for e in related]
        fingerprint = sha256(
            f"SF-AUTH-002|{current['source_ip']}|{','.join(distinct_users)}|{ids[0]}|{ids[-1]}".encode()
        ).hexdigest()
        alerts.append({
            "rule_id": "SF-AUTH-002",
            "fingerprint": fingerprint,
            "title": "One source accessed multiple accounts",
            "severity": "medium",
            "description": (
                f"Events from {current['source_ip']} involved {len(distinct_users)} distinct "
                "usernames within 10 minutes. This may indicate password spraying or account "
                "enumeration; correlate with success events and expected NAT/proxy behavior."
            ),
            "evidence": ids,
            "source_ip": current["source_ip"],
            "username": None,
            "first_seen": related[0]["timestamp"],
            "last_seen": related[-1]["timestamp"],
        })
    return alerts
