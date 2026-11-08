from pathlib import Path

from sentinelforge.db import get_metrics, init_db, insert_event


def test_empty_database_metrics_have_zero_totals(tmp_path: Path):
    path = tmp_path / "empty.sqlite3"
    init_db(path)
    result = get_metrics(path)
    assert result["events"]["total"] == 0
    assert result["events"]["by_type"] == {}
    assert result["events"]["latest_at"] is None
    assert result["alerts"]["total"] == 0
    assert result["alerts"]["by_status"] == {}


def test_metrics_latest_timestamp_tracks_latest_inserted_event(tmp_path: Path):
    path = tmp_path / "timestamps.sqlite3"
    init_db(path)
    for stamp in ("2026-11-01T10:00:00+00:00", "2026-11-01T11:00:00+00:00"):
        insert_event({"timestamp": stamp, "event_type": "login_success",
                      "username": "demo", "source_ip": "192.0.2.1", "host": "lab"}, path)
    assert get_metrics(path)["events"]["latest_at"] == "2026-11-01T11:00:00+00:00"