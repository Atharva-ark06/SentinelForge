import sqlite3
from pathlib import Path

from sentinelforge.db import init_db, list_alerts


def test_legacy_alert_row_survives_additive_migration(tmp_path: Path):
    path = tmp_path / "old.sqlite3"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE events (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL, username TEXT NOT NULL,
            source_ip TEXT NOT NULL, host TEXT NOT NULL
        );
        CREATE TABLE alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id TEXT NOT NULL,
            fingerprint TEXT NOT NULL UNIQUE, title TEXT NOT NULL,
            severity TEXT NOT NULL, description TEXT NOT NULL,
            evidence_json TEXT NOT NULL, source_ip TEXT NOT NULL,
            username TEXT, first_seen TEXT NOT NULL, last_seen TEXT NOT NULL
        );
        INSERT INTO alerts VALUES (
            1,'SF-AUTH-001','legacy-fingerprint','Legacy alert','medium',
            'old row retained','[10,11]','192.0.2.9','demo',
            '2026-10-01T10:00:00+00:00','2026-10-01T10:05:00+00:00'
        );
    """)
    conn.close()
    init_db(path)
    rows = list_alerts(10, path)
    assert len(rows) == 1
    assert rows[0]["id"] == 1
    assert rows[0]["status"] == "new"
    assert rows[0]["evidence"] == [10, 11]