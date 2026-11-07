import json
from pathlib import Path

import pytest

from scripts.windows_sensor import eligible_event, load_checkpoint, parse_event, save_checkpoint, send_event


def event_xml(event_id=4625, record_id=123, username="alice", ip="192.0.2.5", logon_type="3"):
    return f'''<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
      <System><EventID>{event_id}</EventID><EventRecordID>{record_id}</EventRecordID>
      <TimeCreated SystemTime="2026-10-28T17:20:06.6342800Z"/><Computer>LAB01</Computer></System>
      <EventData><Data Name="TargetUserName">{username}</Data><Data Name="IpAddress">{ip}</Data>
      <Data Name="LogonType">{logon_type}</Data></EventData></Event>'''


def test_parse_failure_event():
    event = parse_event(event_xml())
    assert event["record_id"] == 123
    assert event["event_id"] == 4625
    assert event["username"] == "alice"
    assert event["source_ip"] == "192.0.2.5"
    assert event["host"] == "LAB01"


def test_eligibility_accepts_remote_event_with_ip():
    event = parse_event(event_xml())
    assert eligible_event(event) == (True, "eligible")


def test_eligibility_skips_local_event_without_fabricating_ip():
    event = parse_event(event_xml(ip="-", username="SYSTEM", logon_type="5"))
    eligible, reason = eligible_event(event)
    assert eligible is False
    assert "no useful account name" in reason or "no usable source IP" in reason


def test_checkpoint_round_trip(tmp_path: Path):
    state_file = tmp_path / "state.json"
    assert load_checkpoint(state_file) is None
    save_checkpoint(state_file, 456)
    assert json.loads(state_file.read_text()) == {"last_record_id": 456}
    assert load_checkpoint(state_file) == 456


def test_parse_rejects_unsupported_event_id():
    with pytest.raises(ValueError, match="Unsupported event ID"):
        parse_event(event_xml(event_id=4799))


def test_send_event_includes_api_key(monkeypatch):
    import json
    import scripts.windows_sensor as sensor

    captured = {}
    class Response:
        status = 201
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return json.dumps({"new_alerts": 1}).encode()

    def fake_urlopen(request, timeout):
        captured["request"] = request
        return Response()

    monkeypatch.setattr(sensor.urllib.request, "urlopen", fake_urlopen)
    event = {"record_id": 7, "event_id": 4625, "timestamp": "2026-11-07T10:00:00Z",
             "username": "lab-user", "source_ip": "192.0.2.10", "host": "lab-win01"}
    assert send_event(event, "http://127.0.0.1:8000/events", "test-key") is True
    assert captured["request"].get_header("X-api-key") == "test-key"
