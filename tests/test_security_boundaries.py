"""Regression tests for the existing API security boundaries."""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from sentinelforge import api


def test_cors_does_not_allow_arbitrary_origin():
    with TestClient(api.app) as client:
        response = client.options(
            "/events",
            headers={
                "Origin": "https://attacker.example",
                "Access-Control-Request-Method": "POST",
            },
        )
    assert response.headers.get("access-control-allow-origin") is None


def test_cors_allows_configured_local_frontend():
    with TestClient(api.app) as client:
        response = client.options(
            "/events",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
    if "http://localhost:5173" in api.ALLOWED_ORIGINS:
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_api_key_rejects_invalid_secret(monkeypatch):
    monkeypatch.setattr(api, "API_KEY", "expected-key")
    class DummyRequest:
        headers = {"X-API-Key": "wrong-key"}
    with pytest.raises(HTTPException) as exc:
        api.require_ingest_key(DummyRequest())
    assert exc.value.status_code == 401


def test_api_key_fails_closed_without_configuration(monkeypatch):
    monkeypatch.setattr(api, "API_KEY", "")
    class DummyRequest:
        headers = {"X-API-Key": "any-key"}
    with pytest.raises(HTTPException) as exc:
        api.require_ingest_key(DummyRequest())
    assert exc.value.status_code == 503
