import json
from pathlib import Path

import pytest

from scripts.windows_sensor import eligible_event, load_checkpoint, parse_event, save_checkpoint


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
