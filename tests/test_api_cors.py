from fastapi.testclient import TestClient

from sentinelforge import api


def test_patch_preflight_is_allowed_for_configured_local_origin(isolated_database):
    with TestClient(api.app) as client:
        response = client.options(
            "/alerts/1/status",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "PATCH",
                "Access-Control-Request-Headers": "content-type,x-api-key",
            },
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
        assert "PATCH" in response.headers["access-control-allow-methods"]