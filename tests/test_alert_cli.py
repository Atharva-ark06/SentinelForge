import json
import sys

from scripts import manage_alert


def test_cli_requires_environment_api_key(monkeypatch):
    monkeypatch.delenv("SENTINELFORGE_API_KEY", raising=False)
    monkeypatch.setattr(sys, "argv", [
        "manage_alert.py", "--alert-id", "1", "--status", "resolved", "--actor", "analyst",
    ])
    try:
        manage_alert.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("CLI should reject a missing API key")


def test_cli_sends_status_payload_without_printing_key(monkeypatch, capsys):
    monkeypatch.setenv("SENTINELFORGE_API_KEY", "unit-test-secret")
    monkeypatch.setattr(sys, "argv", [
        "manage_alert.py", "--alert-id", "8", "--status", "acknowledged",
        "--actor", "analyst", "--note", "triage",
    ])
    captured = {}

    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self):
            return json.dumps({"id": 8, "status": "acknowledged"}).encode()

    def fake_urlopen(request, timeout):
        captured["request"] = request
        return Response()

    monkeypatch.setattr(manage_alert, "urlopen", fake_urlopen)
    assert manage_alert.main() == 0
    assert captured["request"].get_method() == "PATCH"
    assert captured["request"].get_header("X-api-key") == "unit-test-secret"
    assert "unit-test-secret" not in capsys.readouterr().out