"""Read access controls prevent telemetry disclosure in protected deployments."""

import pytest
from fastapi.testclient import TestClient

from sentinelforge import api


@pytest.mark.parametrize("path", ["/events", "/alerts", "/metrics", "/alerts/1/activity"])
def test_protected_reads_reject_missing_or_wrong_keys(isolated_database, monkeypatch, path):
    monkeypatch.setattr(api, "PROTECT_READS", True)
    with TestClient(api.app) as client:
        assert client.get(path).status_code == 401
        assert client.get(path, headers={"X-API-Key": "wrong"}).status_code == 401


@pytest.mark.parametrize("path", ["/events", "/alerts", "/metrics"])
def test_protected_reads_allow_configured_key(isolated_database, monkeypatch, path):
    monkeypatch.setattr(api, "PROTECT_READS", True)
    with TestClient(api.app) as client:
        assert client.get(path, headers={"X-API-Key": "test-secret"}).status_code == 200


def test_protected_reads_fail_closed_without_key(isolated_database, monkeypatch):
    monkeypatch.setattr(api, "PROTECT_READS", True)
    monkeypatch.setattr(api, "API_KEY", "")
    with TestClient(api.app) as client:
        assert client.get("/events").status_code == 503
        assert client.get("/health").status_code == 200


def test_default_read_behavior_remains_compatible(isolated_database, monkeypatch):
    monkeypatch.setattr(api, "PROTECT_READS", False)
    with TestClient(api.app) as client:
        assert client.get("/events").status_code == 200


@pytest.mark.parametrize("username", ["%", "_", "\\", "a%b", "a_b", "a\\b"])
def test_username_search_treats_wildcards_as_literals(isolated_database, username):
    from sentinelforge.db import insert_event
    from sentinelforge.db import init_db

    init_db(isolated_database)
    insert_event({
        "timestamp": "2026-11-17T10:00:00+00:00",
        "event_type": "login_failure",
        "username": "ordinary-user",
        "source_ip": "192.0.2.1",
        "host": "test-host",
    }, isolated_database)
    with TestClient(api.app) as client:
        response = client.get("/events", params={"username": username})
        assert response.status_code == 200
        assert response.json() == []
