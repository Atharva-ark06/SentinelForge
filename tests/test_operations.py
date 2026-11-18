"""Operational API and seed regression tests."""

from fastapi.testclient import TestClient

from sentinelforge.api import app
from sentinelforge.db import connection, init_db, list_alert_activity
from sentinelforge.observability import new_request_id
from scripts.seed import seed


def test_health_includes_database_status():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert len(response.headers["X-Request-ID"]) == 32
    assert response.headers["Cache-Control"] == "no-store"


def test_api_docs_available_when_enabled():
    with TestClient(app) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "/health" in response.json()["paths"]


def test_seed_is_safe_and_repeatable_with_explicit_force(tmp_path):
    path = tmp_path / "demo.sqlite3"
    assert seed(path) == 12
    try:
        seed(path)
    except ValueError:
        pass
    else:
        raise AssertionError("seed should refuse a nonempty database")
    assert seed(path, force=True) == 12
    with connection(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 24


def test_activity_pagination_empty(tmp_path):
    path = tmp_path / "activity.sqlite3"
    init_db(path)
    assert list_alert_activity(1234, path, limit=1, offset=0) == []


def test_request_ids_are_unique():
    assert new_request_id() != new_request_id()
