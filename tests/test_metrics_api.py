from fastapi.testclient import TestClient

from sentinelforge import api


def test_metrics_endpoint_returns_empty_database_shape(isolated_database):
    with TestClient(api.app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.json()["events"]["total"] == 0
        assert response.json()["alerts"]["total"] == 0


def test_health_endpoint_reports_service_and_timestamp(isolated_database):
    with TestClient(api.app) as client:
        result = client.get("/health").json()
        assert result["status"] == "ok"
        assert result["service"] == "sentinelforge-api"
        assert result["time"]