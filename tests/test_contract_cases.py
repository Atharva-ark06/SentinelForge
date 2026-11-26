"""Data-driven regression cases for ingest auth, parsing, and query validation."""
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sentinelforge import api
from sentinelforge.rate_limit import FixedWindowLimiter

CASE_DIR = Path(__file__).resolve().parent / "contract_cases"
CASES = sorted(CASE_DIR.glob("SF-*.json"))


@pytest.mark.parametrize("case_file", CASES, ids=lambda item: item.stem)
def test_contract_case(case_file, isolated_database, monkeypatch):
    case = json.loads(case_file.read_text(encoding="utf-8"))
    assert case["synthetic"] is True
    assert case["case_id"] == case_file.stem
    monkeypatch.setattr(api, "READ_LIMITER", FixedWindowLimiter(limit=1000))
    monkeypatch.setattr(api, "WRITE_LIMITER", FixedWindowLimiter(limit=1000))
    event = {
        "timestamp": "2026-11-23T09:00:00Z",
        "event_type": "login_failure",
        "username": f"demo-{case['case_id'].lower()}",
        "source_ip": "192.0.2.20",
        "host": "lab-host",
    }
    with TestClient(api.app) as client:
        if case["kind"] == "ingest_valid":
            event.update(case["changes"])
            response = client.post("/events", headers={"X-API-Key": "test-secret"}, json=event)
            assert response.status_code == 201
            assert response.json()["accepted"] is True
            saved = client.get("/events", headers={"X-API-Key": "test-secret"})
            assert saved.status_code == 200
            assert len(saved.json()) == 1
            for key, value in case["changes"].items():
                assert saved.json()[0][key] == value
        elif case["kind"] == "ingest_invalid":
            event.update(case["changes"])
            for key in case.get("remove", []):
                event.pop(key, None)
            response = client.post("/events", headers={"X-API-Key": "test-secret"}, json=event)
            assert response.status_code == 422
            assert client.get("/events").json() == []
        elif case["kind"] == "auth_reject":
            response = client.post("/events", headers={"X-API-Key": case["key"]}, json=event)
            assert response.status_code == 401
            assert client.get("/events").json() == []
        elif case["kind"] == "query_valid":
            response = client.get(case["path"], headers={"X-API-Key": "test-secret"})
            assert response.status_code == 200
            assert isinstance(response.json(), (list, dict))
        elif case["kind"] == "read_auth_protected":
            monkeypatch.setattr(api, "PROTECT_READS", True)
            response = client.get(case["path"], headers={"X-API-Key": case["key"]})
            assert response.status_code == case["status"]
            assert "detail" in response.json()
        elif case["kind"] == "query_invalid":
            response = client.get(case["path"], headers={"X-API-Key": "test-secret"})
            assert response.status_code == case["status"]
            assert "detail" in response.json()
        else:
            raise AssertionError(f"Unrecognized contract case: {case['kind']}")
