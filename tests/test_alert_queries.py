from pathlib import Path

from sentinelforge.db import init_db, insert_alert, list_alerts


def alert(index: int, severity: str, source: str):
    return {
        "rule_id": f"SF-TEST-{index}", "fingerprint": f"fp-{index}",
        "title": "Synthetic test alert", "severity": severity,
        "description": "Synthetic evidence only", "evidence": [index],
        "source_ip": source, "username": None,
        "first_seen": f"2026-11-01T10:0{index}:00+00:00",
        "last_seen": f"2026-11-01T10:0{index}:00+00:00",
    }


def test_alert_filters_run_before_limit_and_offset(tmp_path: Path):
    path = tmp_path / "alerts.sqlite3"
    init_db(path)
    insert_alert(alert(1, "medium", "192.0.2.1"), path)
    insert_alert(alert(2, "high", "192.0.2.2"), path)
    insert_alert(alert(3, "medium", "192.0.2.3"), path)
    rows = list_alerts(1, path, offset=1, severity="medium")
    assert len(rows) == 1
    assert rows[0]["source_ip"] == "192.0.2.1"


def test_alert_status_filter_returns_new_by_default(tmp_path: Path):
    path = tmp_path / "status.sqlite3"
    init_db(path)
    insert_alert(alert(1, "medium", "192.0.2.1"), path)
    assert list_alerts(10, path, status="new")[0]["status"] == "new"
    assert list_alerts(10, path, status="resolved") == []