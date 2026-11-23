"""Data-driven regression cases for ingest auth, parsing, and query validation.

Each fixture is independently executable with an isolated SQLite database.
All data is synthetic; IP addresses belong to RFC 5737 documentation ranges.
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sentinelforge import api

CASE_DIR = Path(__file__).resolve().parent / "contract_cases"
CASES = sorted(CASE_DIR.glob("SF-*.json"))


@pytest.mark.parametrize("case_file", CASES, ids=lambda item: item.stem)
def test_contract_case(case_file, isolated_database):
    case = json.loads(case_file.read_text(encoding="utf-8"))
    assert case["synthetic"] is True
    assert case["case_id"] == case_file.stem
    event = {
        "timestamp": "2026-11-23T09:00:00Z",
        "event_type": "login_failure",
        "username": f"demo-{case['case_id'].lower()}",
        "source_ip": "192.0.2.20",
        "host": "lab-host",
    }
    kind = case["kind"]
    with TestClient(api.app) as client:
        if kind == "ingest_valid":
            event.update(case["changes"])
            response = client.post("/events", headers={"X-API-Key": "test-secret"}, json=event)
            assert response.status_code == 201
            assert response.json()["accepted"] is True
            saved = client.get("/events", headers={"X-API-Key": "test-secret"})
            assert saved.status_code == 200
            assert len(saved.json()) == 1
            for key, value in case["changes"].items():
                assert saved.json()[0][key] == value
        elif kind == "ingest_invalid":
            event.update(case["changes"])
            for key in case.get("remove", []):
                event.pop(key, None)
            response = client.post("/events", headers={"X-API-Key": "test-secret"}, json=event)
            assert response.status_code == 422
            assert client.get("/events").json() == []
        elif kind == "auth_reject":
            response = client.post("/events", headers={"X-API-Key": case["key"]}, json=event)
            assert response.status_code == 401
            assert client.get("/events").json() == []
        elif kind == "query_invalid":
            response = client.get(case["path"], headers={"X-API-Key": "test-secret"})
            assert response.status_code == case["status"]
            assert "detail" in response.json()
        else:
            raise AssertionError(f"Unrecognized contract case: {kind}")
