"""API-key rejection and security response regression coverage."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sentinelforge import api


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(api, "DB_PATH", tmp_path / "auth-boundary.sqlite3")
    monkeypatch.setattr(api, "API_KEY", "test-secret")
    monkeypatch.setattr(api, "API_KEY_CURRENT", "")
    monkeypatch.setattr(api, "API_KEY_PREVIOUS", "")
    with TestClient(api.app) as test_client:
        yield test_client


def event():
    return {"timestamp": "2026-10-28T10:00:00Z",
            "event_type": "login_failure", "username": "demo",
            "source_ip": "192.0.2.22", "host": "test-host"}


def test_oversized_api_key_is_rejected(client):
    response = client.post("/events", headers={"X-API-Key": "x" * 4097}, json=event())
    assert response.status_code == 401


def test_wrong_key_does_not_echo_secret(client):
    response = client.post("/events", headers={"X-API-Key": "sensitive-guess"}, json=event())
    assert response.status_code == 401
    assert "sensitive-guess" not in response.text


def test_valid_key_remains_accepted(client):
    response = client.post("/events", headers={"X-API-Key": "test-secret"}, json=event())
    assert response.status_code == 201


def test_security_headers_are_returned_for_rejections(client):
    response = client.post("/events", headers={"X-API-Key": "invalid"}, json=event())
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Permitted-Cross-Domain-Policies"] == "none"
    assert response.headers["Cross-Origin-Resource-Policy"] == "same-site"
    assert response.headers["Cache-Control"] == "no-store"
