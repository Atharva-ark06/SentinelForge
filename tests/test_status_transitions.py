from pathlib import Path

import pytest

from sentinelforge.db import init_db, insert_alert, update_alert_status


def make_alert():
    return {
        "rule_id": "SF-TEST", "fingerprint": "transition-fingerprint",
        "title": "Transition test", "severity": "medium",
        "description": "Synthetic", "evidence": [1], "source_ip": "192.0.2.1",
        "username": "demo", "first_seen": "2026-11-01T00:00:00+00:00",
        "last_seen": "2026-11-01T00:00:00+00:00",
    }


@pytest.mark.parametrize("sequence", [
    ["acknowledged", "investigating", "resolved"],
    ["false_positive", "new", "investigating"],
    ["resolved", "new", "acknowledged"],
])
def test_valid_lifecycle_sequences(tmp_path: Path, sequence):
    path = tmp_path / "sequence.sqlite3"
    init_db(path)
    insert_alert(make_alert(), path)
    for status in sequence:
        assert update_alert_status(1, status, "test-analyst", db_path=path)["status"] == status


@pytest.mark.parametrize("first,second", [
    ("resolved", "false_positive"),
    ("false_positive", "resolved"),
    ("investigating", "new"),
])
def test_invalid_lifecycle_sequences_are_rejected(tmp_path: Path, first, second):
    path = tmp_path / "invalid.sqlite3"
    init_db(path)
    insert_alert(make_alert(), path)
    update_alert_status(1, first, "test-analyst", db_path=path)
    with pytest.raises(ValueError):
        update_alert_status(1, second, "test-analyst", db_path=path)