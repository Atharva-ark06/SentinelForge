import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

DEFAULT_DB = Path(os.environ.get("SENTINELFORGE_DB", "sentinelforge.sqlite3"))
ALERT_STATUSES = {"new", "acknowledged", "investigating", "resolved", "false_positive"}
ALERT_TRANSITIONS = {
    "new": {"acknowledged", "investigating", "resolved", "false_positive"},
    "acknowledged": {"new", "investigating", "resolved", "false_positive"},
    "investigating": {"acknowledged", "resolved", "false_positive"},
    "resolved": {"new", "investigating"},
    "false_positive": {"new"},
}


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


@contextmanager
def connection(db_path: str | Path | None = None):
    """Yield a SQLite connection that commits/rolls back and always closes."""
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str | Path | None = None) -> None:
    with connection(db_path) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL CHECK(event_type IN ('login_success','login_failure')),
            username TEXT NOT NULL,
            source_ip TEXT NOT NULL,
            host TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_events_time ON events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_events_source_time ON events(source_ip, timestamp);
        CREATE INDEX IF NOT EXISTS idx_events_user_time ON events(username, timestamp);
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT NOT NULL,
            fingerprint TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT NOT NULL,
            evidence_json TEXT NOT NULL,
            source_ip TEXT NOT NULL,
            username TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_alerts_last_seen ON alerts(last_seen);
        """)
        # Additive migrations preserve existing SQLite databases.
        alert_columns = {row["name"] for row in conn.execute("PRAGMA table_info(alerts)")}
        if "status" not in alert_columns:
            conn.execute("ALTER TABLE alerts ADD COLUMN status TEXT NOT NULL DEFAULT 'new'")
        if "updated_at" not in alert_columns:
            conn.execute("ALTER TABLE alerts ADD COLUMN updated_at TEXT")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alert_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
                previous_status TEXT,
                new_status TEXT NOT NULL,
                actor TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alert_activity_alert ON alert_activity(alert_id, id)")


def insert_event(event: dict[str, Any], db_path: str | Path | None = None) -> int:
    with connection(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO events(timestamp,event_type,username,source_ip,host)
               VALUES(?,?,?,?,?)""",
            (event["timestamp"], event["event_type"], event["username"],
             event["source_ip"], event["host"]),
        )
        return int(cur.lastrowid)


def _filters(clauses: list[str], values: list[Any], *, event_type=None,
             username=None, source_ip=None, start=None, end=None):
    if event_type:
        clauses.append("event_type = ?"); values.append(event_type)
    if username:
        clauses.append("username LIKE ?"); values.append(f"%{username}%")
    if source_ip:
        clauses.append("source_ip = ?"); values.append(source_ip)
    if start:
        clauses.append("timestamp >= ?"); values.append(start)
    if end:
        clauses.append("timestamp <= ?"); values.append(end)


def list_events(limit: int = 100, db_path: str | Path | None = None, *,
                offset: int = 0, event_type: str | None = None,
                username: str | None = None, source_ip: str | None = None,
                start: str | None = None, end: str | None = None) -> list[dict[str, Any]]:
    clauses: list[str] = []
    values: list[Any] = []
    _filters(clauses, values, event_type=event_type, username=username,
             source_ip=source_ip, start=start, end=end)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    values.extend([limit, offset])
    with connection(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM events{where} ORDER BY timestamp DESC, id DESC LIMIT ? OFFSET ?", values
        ).fetchall()
        return [dict(row) for row in rows]


def list_alerts(limit: int = 100, db_path: str | Path | None = None, *,
                offset: int = 0, severity: str | None = None,
                status: str | None = None, source_ip: str | None = None) -> list[dict[str, Any]]:
    import json
    clauses: list[str] = []
    values: list[Any] = []
    for field, value in (("severity", severity), ("status", status), ("source_ip", source_ip)):
        if value:
            clauses.append(f"{field} = ?"); values.append(value)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    values.extend([limit, offset])
    with connection(db_path) as conn:
        rows = conn.execute(
            f"SELECT * FROM alerts{where} ORDER BY last_seen DESC, id DESC LIMIT ? OFFSET ?", values
        ).fetchall()
        output = []
        for row in rows:
            item = dict(row)
            item["evidence"] = json.loads(item.pop("evidence_json"))
            output.append(item)
        return output


def insert_alert(alert: dict[str, Any], db_path: str | Path | None = None) -> bool:
    import json
    with connection(db_path) as conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO alerts
               (rule_id,fingerprint,title,severity,description,evidence_json,
                source_ip,username,first_seen,last_seen)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (alert["rule_id"], alert["fingerprint"], alert["title"],
             alert["severity"], alert["description"], json.dumps(alert["evidence"]),
             alert["source_ip"], alert.get("username"), alert["first_seen"],
             alert["last_seen"]),
        )
        return cur.rowcount == 1


def update_alert_status(alert_id: int, new_status: str, actor: str, note: str = "",
                        db_path: str | Path | None = None) -> dict[str, Any] | None:
    import json
    from datetime import datetime, timezone
    if new_status not in ALERT_STATUSES:
        raise ValueError("Unsupported alert status")
    if not actor.strip() or len(actor) > 128:
        raise ValueError("actor must contain 1-128 non-whitespace characters")
    if len(note) > 1000:
        raise ValueError("note must be 1000 characters or fewer")
    now = datetime.now(timezone.utc).isoformat()
    with connection(db_path) as conn:
        row = conn.execute("SELECT status FROM alerts WHERE id = ?", (alert_id,)).fetchone()
        if row is None:
            return None
        previous = row["status"]
        if new_status == previous:
            raise ValueError("Alert already has this status")
        if new_status not in ALERT_TRANSITIONS.get(previous, set()):
            raise ValueError(f"Cannot move alert from {previous} to {new_status}")
        conn.execute("UPDATE alerts SET status = ?, updated_at = ? WHERE id = ?",
                     (new_status, now, alert_id))
        conn.execute("""INSERT INTO alert_activity
            (alert_id, previous_status, new_status, actor, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (alert_id, previous, new_status, actor.strip(), note.strip(), now))
        updated = conn.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,)).fetchone()
        item = dict(updated)
        item["evidence"] = json.loads(item.pop("evidence_json"))
        return item


def list_alert_activity(alert_id: int, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    with connection(db_path) as conn:
        rows = conn.execute(
            """SELECT id, alert_id, previous_status, new_status, actor, note, created_at
               FROM alert_activity WHERE alert_id = ? ORDER BY id DESC""", (alert_id,)
        ).fetchall()
        return [dict(row) for row in rows]


def get_metrics(db_path: str | Path | None = None) -> dict[str, Any]:
    with connection(db_path) as conn:
        event_total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        event_counts = {row["event_type"]: row["count"] for row in conn.execute(
            "SELECT event_type, COUNT(*) AS count FROM events GROUP BY event_type")}
        alert_total = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
        alert_counts = {row["severity"]: row["count"] for row in conn.execute(
            "SELECT severity, COUNT(*) AS count FROM alerts GROUP BY severity")}
        status_counts = {row["status"]: row["count"] for row in conn.execute(
            "SELECT status, COUNT(*) AS count FROM alerts GROUP BY status")}
        latest_event = conn.execute("SELECT MAX(timestamp) FROM events").fetchone()[0]
        latest_alert = conn.execute("SELECT MAX(last_seen) FROM alerts").fetchone()[0]
    return {
        "events": {"total": event_total, "by_type": event_counts,
                   "latest_at": latest_event},
        "alerts": {"total": alert_total, "by_severity": alert_counts,
                   "by_status": status_counts, "latest_at": latest_alert},
    }
