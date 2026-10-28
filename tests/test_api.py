from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from sentinelforge import api


@pytest.fixture(autouse=True)
def isolated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "sentinelforge-test.sqlite3"
    monkeypatch.setattr(api, "DB_PATH", db_path)
    yield


def test_health():
    with TestClient(api.app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_ingests_event_and_lists_it():
    with TestClient(api.app) as client:
        response = client.post("/events", json={
            "timestamp": "2026-10-28T10:00:00Z", "event_type": "login_success",
            "username": "alice", "source_ip": "192.0.2.1", "host": "lab01",
        })
        assert response.status_code == 201
        assert response.json()["accepted"] is True
        events = client.get("/events").json()
        assert len(events) == 1
        assert events[0]["username"] == "alice"


def test_repeated_failures_generate_explainable_alert():
    with TestClient(api.app) as client:
        for i in range(5):
            response = client.post("/events", json={
                "timestamp": f"2026-10-28T10:0{i}:00Z", "event_type": "login_failure",
                "username": "admin", "source_ip": "192.0.2.20", "host": "lab01",
            })
            assert response.status_code == 201
        alerts = client.get("/alerts").json()
        alert = next(a for a in alerts if a["rule_id"] == "SF-AUTH-001")
        assert len(alert["evidence"]) == 5
        assert "may indicate password guessing" in alert["description"]


def test_rejects_invalid_ip_and_naive_timestamp():
    with TestClient(api.app) as client:
        base = {"timestamp": "2026-10-28T10:00:00Z", "event_type": "login_failure",
                "username": "admin", "source_ip": "192.0.2.20", "host": "lab01"}
        bad_ip = {**base, "source_ip": "not-an-ip"}
        naive_time = {**base, "timestamp": "2026-10-28T10:00:00"}
        assert client.post("/events", json=bad_ip).status_code == 422
        assert client.post("/events", json=naive_time).status_code == 422


def test_multi_account_source_rule():
    with TestClient(api.app) as client:
        for i, username in enumerate(["alice", "bob", "charlie"]):
            response = client.post("/events", json={
                "timestamp": f"2026-10-28T11:0{i}:00Z", "event_type": "login_failure",
                "username": username, "source_ip": "198.51.100.9", "host": "lab01",
            })
            assert response.status_code == 201
        assert any(a["rule_id"] == "SF-AUTH-002" for a in client.get("/alerts").json())


def test_rejects_unknown_fields():
    with TestClient(api.app) as client:
        response = client.post("/events", json={
            "timestamp": "2026-10-28T10:00:00Z", "event_type": "login_success",
            "username": "alice", "source_ip": "192.0.2.1", "host": "lab01",
            "password": "should-not-be-accepted",
        })
        assert response.status_code == 422
