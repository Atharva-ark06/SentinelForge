"""Regression coverage for failure-only detection and event traceability."""

from fastapi.testclient import TestClient

from sentinelforge import api


def _event(kind: str, username: str, minute: int):
    return {
        "timestamp": f"2026-11-25T09:{minute:02d}:00Z",
        "event_type": kind,
        "username": username,
        "source_ip": "192.0.2.61",
        "host": "demo-host",
    }


def test_success_after_failure_threshold_does_not_create_extra_alerts(isolated_database):
    with TestClient(api.app) as client:
        client.headers.update({"X-API-Key": "test-secret"})
        for index in range(5):
            assert client.post("/events", json=_event("login_failure", "alice", index)).status_code == 201
        before = client.get("/alerts").json()
        response = client.post("/events", json=_event("login_success", "alice", 5))
        assert response.status_code == 201
        assert response.json()["new_alerts"] == 0
        assert response.json()["detections"] == []
        assert client.get("/alerts").json() == before


def test_successful_accounts_do_not_count_as_password_spray(isolated_database):
    with TestClient(api.app) as client:
        client.headers.update({"X-API-Key": "test-secret"})
        for index, username in enumerate(("alice", "bob", "charlie", "dave")):
            response = client.post("/events", json=_event("login_success", username, index))
            assert response.status_code == 201
            assert response.json()["detections"] == []
        assert client.post("/events", json=_event("login_failure", "erin", 5)).status_code == 201
        assert client.get("/alerts").json() == []


def test_two_failed_users_and_one_success_remain_below_spray_threshold(isolated_database):
    with TestClient(api.app) as client:
        client.headers.update({"X-API-Key": "test-secret"})
        for index, (kind, username) in enumerate((
            ("login_failure", "alice"),
            ("login_failure", "bob"),
            ("login_success", "carol"),
        )):
            assert client.post("/events", json=_event(kind, username, index)).status_code == 201
        assert client.get("/alerts").json() == []
