from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from sentinelforge import api


@pytest.fixture(autouse=True)
def isolated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "sentinelforge-test.sqlite3"
    monkeypatch.setattr(api, "DB_PATH", db_path)
    monkeypatch.setattr(api, "API_KEY", "test-secret")
    yield


def test_health():
    with TestClient(api.app) as client:
        client.headers.update({"X-API-Key": "test-secret"})
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_ingests_event_and_lists_it():
    with TestClient(api.app) as client:
        client.headers.update({"X-API-Key": "test-secret"})
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
        client.headers.update({"X-API-Key": "test-secret"})
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
        client.headers.update({"X-API-Key": "test-secret"})
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


def test_ingestion_fails_closed_without_configured_key(monkeypatch):
    monkeypatch.setattr(api, "API_KEY", "")
    with TestClient(api.app) as client:
        response = client.post("/events", json={
            "timestamp": "2026-10-28T10:00:00Z", "event_type": "login_success",
            "username": "alice", "source_ip": "192.0.2.1", "host": "lab01",
        })
        assert response.status_code == 503


def test_ingestion_rejects_wrong_api_key():
    with TestClient(api.app) as client:
        response = client.post("/events", headers={"X-API-Key": "wrong-key"}, json={
            "timestamp": "2026-10-28T10:00:00Z", "event_type": "login_success",
            "username": "alice", "source_ip": "192.0.2.1", "host": "lab01",
        })
        assert response.status_code == 401


def test_metrics_are_database_wide_and_include_alert_statuses():
    with TestClient(api.app) as client:
        client.headers.update({"X-API-Key": "test-secret"})
        for i in range(3):
            client.post("/events", json={
                "timestamp": f"2026-10-28T10:0{i}:00Z", "event_type": "login_failure",
                "username": "admin", "source_ip": "192.0.2.44", "host": "lab01",
            })
        metrics = client.get("/metrics")
        assert metrics.status_code == 200
        data = metrics.json()
        assert data["events"]["total"] == 3
        assert data["events"]["by_type"]["login_failure"] == 3
        assert data["alerts"]["by_status"].get("new", 0) == 0


def test_event_filters_and_offset_pagination():
    with TestClient(api.app) as client:
        client.headers.update({"X-API-Key": "test-secret"})
        for i, (user, kind) in enumerate([
            ("alice", "login_success"), ("bob", "login_failure"),
            ("alice", "login_failure"), ("charlie", "login_success"),
        ]):
            client.post("/events", json={
                "timestamp": f"2026-10-28T10:0{i}:00Z", "event_type": kind,
                "username": user, "source_ip": "192.0.2.55", "host": "lab01",
            })
        filtered = client.get("/events", params={
            "event_type": "login_failure", "username": "ali", "limit": 1,
        })
        assert filtered.status_code == 200
        assert len(filtered.json()) == 1
        assert filtered.json()[0]["username"] == "alice"
        page = client.get("/events", params={"limit": 2, "offset": 1})
        assert len(page.json()) == 2
        assert page.json()[0]["id"] > page.json()[1]["id"]


def test_alert_status_transition_is_audited_and_filterable():
    with TestClient(api.app) as client:
        client.headers.update({"X-API-Key": "test-secret"})
        for i in range(5):
            client.post("/events", json={
                "timestamp": f"2026-10-28T10:0{i}:00Z", "event_type": "login_failure",
                "username": "admin", "source_ip": "192.0.2.66", "host": "lab01",
            })
        alert = next(a for a in client.get("/alerts").json()
                     if a["rule_id"] == "SF-AUTH-001")
        changed = client.patch(f"/alerts/{alert['id']}/status", json={
            "status": "acknowledged", "actor": "analyst@example.test",
            "note": "Investigating in the lab",
        })
        assert changed.status_code == 200
        assert changed.json()["status"] == "acknowledged"
        history = client.get(f"/alerts/{alert['id']}/activity")
        assert history.status_code == 200
        assert history.json()[0]["previous_status"] == "new"
        assert history.json()[0]["new_status"] == "acknowledged"
        assert history.json()[0]["actor"] == "analyst@example.test"
        assert client.get("/alerts", params={"status": "acknowledged"}).json()[0]["id"] == alert["id"]


def test_alert_status_requires_ingestion_key():
    with TestClient(api.app) as client:
        response = client.patch("/alerts/1/status", json={
            "status": "resolved", "actor": "analyst", "note": "",
        })
        assert response.status_code == 401


def test_alert_status_rejects_invalid_transition_payload():
    with TestClient(api.app) as client:
        client.headers.update({"X-API-Key": "test-secret"})
        response = client.patch("/alerts/1/status", json={
            "status": "deleted", "actor": "analyst",
        })
        assert response.status_code == 422
