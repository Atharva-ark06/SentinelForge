from fastapi.testclient import TestClient

from sentinelforge import api


def test_event_filter_rejects_invalid_event_type(isolated_database):
    with TestClient(api.app) as client:
        assert client.get("/events", params={"event_type": "password_reset"}).status_code == 422


def test_event_filter_rejects_invalid_source_ip(isolated_database):
    with TestClient(api.app) as client:
        assert client.get("/events", params={"source_ip": "not-an-ip"}).status_code == 400


def test_event_pagination_caps_page_size(isolated_database):
    with TestClient(api.app) as client:
        assert client.get("/events", params={"limit": 1001}).status_code == 422
        assert client.get("/events", params={"offset": -1}).status_code == 422

def test_event_time_filter_requires_timezone(isolated_database):
    with TestClient(api.app) as client:
        response = client.get("/events", params={"start": "2026-10-28T10:00:00"})
        assert response.status_code == 400
        assert "timezone" in response.json()["detail"]
