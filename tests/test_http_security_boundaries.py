"""Security headers and browser origin regression tests."""
from fastapi.testclient import TestClient
from sentinelforge import api


def test_dashboard_csp_nonce_is_substituted():
    with TestClient(api.app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "__CSP_NONCE__" not in response.text
        assert "script-src 'nonce-" in response.headers["Content-Security-Policy"]
        assert "<script nonce=\"" in response.text


def test_sensitive_response_headers_are_present():
    with TestClient(api.app) as client:
        response = client.get("/health")
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Referrer-Policy"] == "no-referrer"
        assert response.headers["Cache-Control"] == "no-store"


def test_untrusted_origin_receives_no_cors_permission():
    with TestClient(api.app) as client:
        response = client.options("/events", headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        })
        assert response.headers.get("access-control-allow-origin") != "https://attacker.example"


def test_allowed_origin_is_explicit():
    with TestClient(api.app) as client:
        response = client.options("/events", headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        })
        assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_host_header_restriction():
    with TestClient(api.app) as client:
        response = client.get("/health", headers={"Host": "attacker.example"})
        assert response.status_code == 400
