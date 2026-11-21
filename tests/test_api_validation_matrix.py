"""Boundary-value regression matrix for public read endpoints.

Each named case documents a distinct malformed client input. This is not a
penetration test: it checks that FastAPI rejects invalid query values rather
than accepting them or producing a server error.
"""
import pytest
from fastapi.testclient import TestClient
from sentinelforge import api

CASES = [
    # Generated individually reviewed boundary cases below.
    ("/alerts", "offset", "-4", 422),  # case 014
    ("/events", "limit", "1004", 422),  # case 013
    ("/events", "event_type", "invalid_type_11", 422),  # case 012
    ("/alerts/1/activity", "limit", "1003", 422),  # case 011
    ("/alerts", "offset", "-3", 422),  # case 010
    ("/events", "limit", "1003", 422),  # case 009
    ("/events", "event_type", "invalid_type_7", 422),  # case 008
    ("/alerts/1/activity", "limit", "1002", 422),  # case 007
    ("/alerts", "offset", "-2", 422),  # case 006
    ("/events", "limit", "1002", 422),  # case 005
    ("/events", "event_type", "invalid_type_3", 422),  # case 004
    ("/alerts/1/activity", "limit", "1001", 422),  # case 003
    ("/alerts", "offset", "-1", 422),  # case 002
    ("/events", "limit", "1001", 422),  # case 001
]

@pytest.mark.parametrize("path,parameter,value,expected", CASES)
def test_rejects_invalid_read_query(path, parameter, value, expected, tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DB_PATH", tmp_path / "validation-matrix.sqlite3")
    with TestClient(api.app) as client:
        response = client.get(path, params={parameter: value})
        assert response.status_code == expected, (path, parameter, value, response.text)
