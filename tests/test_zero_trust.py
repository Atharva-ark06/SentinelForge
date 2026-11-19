"""Security regression checks for CSP, rotation, and SQLite data-only access."""

import re
import sqlite3

import pytest
from fastapi.testclient import TestClient

from sentinelforge import api
from sentinelforge.db import connection


def test_nonce_changes_per_response(isolated_database):
    with TestClient(api.app) as client:
        first = client.get("/")
        second = client.get("/")
        for response in (first, second):
            nonce = re.search(r"script-src 'nonce-([^']+)'", response.headers["content-security-policy"])
            assert nonce
            assert f'<script nonce="{nonce.group(1)}">' in response.text
            assert f'<style nonce="{nonce.group(1)}">' in response.text
            assert "'unsafe-inline'" not in response.headers["content-security-policy"]
        assert first.headers["content-security-policy"] != second.headers["content-security-policy"]


def test_api_key_rotation_accepts_only_active_keys(monkeypatch):
    monkeypatch.setattr(api, "API_KEY_CURRENT", "active-secret")
    monkeypatch.setattr(api, "API_KEY_PREVIOUS", "retiring-secret")
    with TestClient(api.app) as client:
        for key in ("active-secret", "retiring-secret"):
            assert client.post("/demo/run", headers={"X-API-Key": key}).status_code == 200
        assert client.post("/demo/run", headers={"X-API-Key": "old-secret"}).status_code == 401


def test_runtime_sql_connection_rejects_ddl(isolated_database):
    with connection(api.DB_PATH) as conn:
        assert conn.execute("SELECT 1").fetchone()[0] == 1
        with pytest.raises(sqlite3.DatabaseError):
            conn.execute("DROP TABLE events")
        with pytest.raises(sqlite3.DatabaseError):
            conn.execute("ATTACH DATABASE ':memory:' AS other")
