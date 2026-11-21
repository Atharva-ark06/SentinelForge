"""Protect sensitive read endpoints when explicitly configured.

The default public synthetic demo must not be confused with production
authorization. These tests ensure protected-read mode covers telemetry and
does not inadvertently lock out the health probe.
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sentinelforge import api


@pytest.fixture
def protected_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(api, "DB_PATH", tmp_path / "protected.sqlite3")
    monkeypatch.setattr(api, "API_KEY", "read-test-secret")
    monkeypatch.setattr(api, "API_KEY_CURRENT", "")
    monkeypatch.setattr(api, "API_KEY_PREVIOUS", "")
    monkeypatch.setattr(api, "PROTECT_READS", True)
    with TestClient(api.app) as client:
        yield client


@pytest.mark.parametrize("path", ["/events", "/alerts", "/metrics"])
def test_protected_telemetry_requires_key(protected_client, path):
    response = protected_client.get(path)
    assert response.status_code == 401


@pytest.mark.parametrize("path", ["/events", "/alerts", "/metrics"])
def test_protected_telemetry_rejects_wrong_key(protected_client, path):
    response = protected_client.get(path, headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


@pytest.mark.parametrize("path", ["/events", "/alerts", "/metrics"])
def test_protected_telemetry_accepts_valid_key(protected_client, path):
    response = protected_client.get(path, headers={"X-API-Key": "read-test-secret"})
    assert response.status_code == 200


def test_health_remains_public_with_protected_reads(protected_client):
    response = protected_client.get("/health")
    assert response.status_code == 200


def test_alert_activity_requires_key_even_for_missing_id(protected_client):
    response = protected_client.get("/alerts/9999/activity")
    assert response.status_code == 401
