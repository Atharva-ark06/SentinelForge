"""Regression coverage for key rotation and failure-only query behavior."""

from fastapi.testclient import TestClient

from sentinelforge import api


def _event(username="demo-user", kind="login_failure", i=0):
    return {
        "timestamp": f"2026-11-26T10:{i:02d}:00Z",
        "event_type": kind,
        "username": username,
        "source_ip": "203.0.113.72",
        "host": "lab-host",
    }


def test_rotation_accepts_current_and_previous_keys(isolated_database, monkeypatch):
    monkeypatch.setattr(api, "API_KEY", "")
    monkeypatch.setattr(api, "API_KEY_CURRENT", "current-test-key")
    monkeypatch.setattr(api, "API_KEY_PREVIOUS", "previous-test-key")
    with TestClient(api.app) as client:
        for i, secret in enumerate(("current-test-key", "previous-test-key")):
            result = client.post("/events", headers={"X-API-Key": secret}, json=_event(i=i))
            assert result.status_code == 201
        assert len(client.get("/events").json()) == 2


def test_rotation_rejects_incorrect_key_without_storage(isolated_database, monkeypatch):
    monkeypatch.setattr(api, "API_KEY_CURRENT", "current-test-key")
    monkeypatch.setattr(api, "API_KEY_PREVIOUS", "previous-test-key")
    with TestClient(api.app) as client:
        for secret in ("", "current-test-key ", "previous-test-key ", "totally-invalid"):
            result = client.post("/events", headers={"X-API-Key": secret}, json=_event())
            assert result.status_code == 401
        assert client.get("/events").json() == []


def test_successful_event_does_not_trigger_spray_rule(isolated_database):
    with TestClient(api.app) as client:
        headers = {"X-API-Key": "test-secret"}
        for i, username in enumerate(("alice", "bob", "charlie", "dave")):
            response = client.post("/events", headers=headers, json=_event(username, "login_success", i))
            assert response.status_code == 201
            assert response.json()["detections"] == []
        assert client.get("/alerts").json() == []
