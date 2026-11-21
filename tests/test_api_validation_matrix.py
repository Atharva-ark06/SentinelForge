"""Boundary-value regression matrix for public read endpoints.

Each named case documents a distinct malformed client input. This is not a
penetration test: it checks that FastAPI rejects invalid query values rather
than accepting them or producing a server error.
"""
import pytest
from fastapi.testclient import TestClient
from sentinelforge import api

CASES = [
    ("/events", "event_type", "login_failure\n", 422),
    ("/events", "limit", "1.5", 422),
    ("/alerts", "source_ip", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", 422),
    ("/events", "source_ip", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", 422),
    ("/events", "username", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", 422),
    ("/alerts", "status", " investigating", 422),
    ("/alerts", "status", "resolved ", 422),
    ("/alerts", "severity", " high", 422),
    ("/alerts", "severity", "medium ", 422),
    ("/events", "event_type", " login_failure", 422),
    ("/events", "event_type", "login_success ", 422),
    ("/alerts/1/activity", "limit", "-1", 422),
    ("/alerts", "limit", "-1", 422),
    ("/events", "limit", "-1", 422),
    ("/alerts", "offset", "999999999999", 422),
    ("/events", "offset", "999999999999", 422),
    ("/alerts/1/activity", "offset", "100001", 422),
    ("/alerts", "offset", "100001", 422),
    ("/events", "offset", "100001", 422),
    ("/alerts/1/activity", "limit", "100000", 422),  # limit boundary 100000
    ("/alerts", "limit", "100000", 422),  # limit boundary 100000
    ("/events", "limit", "100000", 422),  # limit boundary 100000
    ("/alerts", "source_ip", "", 422),  # source_ip boundary 
    ("/events", "source_ip", "", 422),  # source_ip boundary 
    ("/events", "username", "", 422),  # username boundary 
    ("/alerts", "status", "NEW", 422),  # status boundary NEW
    ("/alerts", "status", "deleted", 422),  # status boundary deleted
    ("/alerts", "severity", "unknown", 422),  # severity boundary unknown
    ("/alerts", "severity", "CRITICAL", 422),  # severity boundary CRITICAL
    ("/events", "event_type", "login-failure", 422),  # event_type boundary login-failure
    ("/events", "event_type", "LOGIN_FAILURE", 422),  # event_type boundary LOGIN_FAILURE
    ("/alerts/1/activity", "offset", "-999", 422),  # offset boundary -999
    ("/alerts", "offset", "-999", 422),  # offset boundary -999
    ("/events", "offset", "-999", 422),  # offset boundary -999
    ("/alerts/1/activity", "limit", "0", 422),  # limit boundary 0
    ("/alerts", "limit", "0", 422),  # limit boundary 0
    ("/events", "limit", "0", 422),  # limit boundary 0
    # Boundary cases intentionally cover distinct invalid query combinations.
    ("/alerts/1/activity", "limit", "1005", 422),  # case 019
    ("/alerts", "offset", "-5", 422),  # case 018
    ("/events", "limit", "1005", 422),  # case 017
    ("/events", "event_type", "invalid_type_15", 422),  # case 016
    ("/alerts/1/activity", "limit", "1004", 422),  # case 015
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
