import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

DEFAULT_DB = Path(os.environ.get("SENTINELFORGE_DB", "sentinelforge.sqlite3"))


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
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


def insert_event(event: dict[str, Any], db_path: str | Path | None = None) -> int:
    with connection(db_path) as conn:
        cur = conn.execute(
            """INSERT INTO events(timestamp,event_type,username,source_ip,host)
               VALUES(?,?,?,?,?)""",
            (event["timestamp"], event["event_type"], event["username"],
             event["source_ip"], event["host"]),
        )
        return int(cur.lastrowid)


def list_events(limit: int = 100, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    with connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY timestamp DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]


def list_alerts(limit: int = 100, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    import json
    with connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM alerts ORDER BY last_seen DESC, id DESC LIMIT ?", (limit,)
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
