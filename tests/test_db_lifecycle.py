from pathlib import Path
import sqlite3

import pytest

from sentinelforge.db import (
    get_metrics,
    init_db,
    insert_alert,
    insert_event,
    list_alert_activity,
    list_alerts,
    list_events,
    update_alert_status,
)


@pytest.fixture
def database(tmp_path: Path) -> Path:
    path = tmp_path / "unit.sqlite3"
    init_db(path)
    return path


def sample_event(index: int, username: str = "alice", event_type: str = "login_failure"):
    return {
        "timestamp": f"2026-11-01T10:{index:02d}:00+00:00",
        "event_type": event_type,
        "username": username,
        "source_ip": "192.0.2.20",
        "host": "lab01",
    }


def sample_alert():
    return {
        "rule_id": "SF-AUTH-001",
        "fingerprint": "unit-test-alert-fingerprint",
        "title": "Repeated authentication failures",
        "severity": "medium",
        "description": "Synthetic test alert",
        "evidence": [1, 2, 3, 4, 5],
        "source_ip": "192.0.2.20",
        "username": "alice",
        "first_seen": "2026-11-01T10:00:00+00:00",
        "last_seen": "2026-11-01T10:04:00+00:00",
    }


def test_event_queries_apply_filter_and_offset(database):
    for i in range(5):
        insert_event(sample_event(i, "alice" if i % 2 == 0 else "bob"), database)
    rows = list_events(2, database, offset=1, username="ali")
    assert len(rows) == 1
    assert rows[0]["username"] == "alice"


def test_event_queries_filter_by_type_and_source(database):
    insert_event(sample_event(1, event_type="login_failure"), database)
    insert_event(sample_event(2, event_type="login_success"), database)
    rows = list_events(10, database, event_type="login_success", source_ip="192.0.2.20")
    assert len(rows) == 1
    assert rows[0]["event_type"] == "login_success"


def test_alert_insert_is_idempotent(database):
    alert = sample_alert()
    assert insert_alert(alert, database) is True
    assert insert_alert(alert, database) is False
    assert len(list_alerts(10, database)) == 1


def test_alert_lifecycle_persists_status_and_actor_history(database):
    insert_alert(sample_alert(), database)
    updated = update_alert_status(1, "acknowledged", "analyst-a", "triage started", database)
    assert updated is not None
    assert updated["status"] == "acknowledged"
    assert updated["evidence"] == [1, 2, 3, 4, 5]
    history = list_alert_activity(1, database)
    assert len(history) == 1
    assert history[0]["previous_status"] == "new"
    assert history[0]["new_status"] == "acknowledged"
    assert history[0]["actor"] == "analyst-a"\n    update_alert_status(1, "investigating", "analyst-a", "continue review", database)
    with pytest.raises(ValueError, match="Cannot move alert"):
        update_alert_status(1, "new", "analyst-a", "invalid backward transition", database)


def test_alert_status_validation_is_fail_closed(database):
    insert_alert(sample_alert(), database)
    with pytest.raises(ValueError):
        update_alert_status(1, "deleted", "analyst", db_path=database)
    with pytest.raises(ValueError):
        update_alert_status(1, "resolved", "   ", db_path=database)
    with pytest.raises(ValueError):
        update_alert_status(1, "resolved", "analyst", "x" * 1001, database)


def test_metrics_return_full_database_counts(database):
    insert_event(sample_event(1), database)
    insert_event(sample_event(2, event_type="login_success"), database)
    insert_alert(sample_alert(), database)
    metrics = get_metrics(database)
    assert metrics["events"]["total"] == 2
    assert metrics["events"]["by_type"] == {"login_failure": 1, "login_success": 1}
    assert metrics["alerts"]["total"] == 1
    assert metrics["alerts"]["by_status"] == {"new": 1}


def test_additive_migration_upgrades_existing_alert_table(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            username TEXT NOT NULL,
            source_ip TEXT NOT NULL,
            host TEXT NOT NULL
        );
        CREATE TABLE alerts (
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
    """)
    conn.close()
    init_db(path)
    conn = sqlite3.connect(path)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(alerts)")}
    activity_table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='alert_activity'"
    ).fetchone()
    conn.close()
    assert {"status", "updated_at"} <= columns
    assert activity_table is not None
