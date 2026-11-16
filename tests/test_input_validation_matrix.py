"""Regression matrix for normalized event input validation."""
import pytest
from pydantic import ValidationError
from sentinelforge.models import SecurityEventIn

CASES = [
    ("source_ip", "192.0.2.1", True),
    ("source_ip", "192.0.2.2", True),
    ("source_ip", "192.0.2.3", True),
    ("source_ip", "192.0.2.4", True),
    ("source_ip", "192.0.2.5", True),
    ("source_ip", "192.0.2.6", True),
    ("source_ip", "192.0.2.7", True),
    ("source_ip", "192.0.2.8", True),
    ("source_ip", "192.0.2.9", True),
    ("source_ip", "192.0.2.10", True),
    ("source_ip", "192.0.2.11", True),
    ("source_ip", "192.0.2.12", True),
    ("source_ip", "192.0.2.13", True),
    ("source_ip", "192.0.2.14", True),
    ("source_ip", "192.0.2.15", True),
    ("source_ip", "192.0.2.16", True),
    ("source_ip", "192.0.2.17", True),
    ("source_ip", "192.0.2.18", True),
    ("source_ip", "192.0.2.19", True),
    ("source_ip", "192.0.2.20", True),
    ("source_ip", "2001:db8::1", True),
    ("source_ip", "2001:db8::2", True),
    ("source_ip", "2001:db8::3", True),
    ("source_ip", "2001:db8::4", True),
    ("source_ip", "2001:db8::5", True),
    ("source_ip", "2001:db8::6", True),
    ("source_ip", "2001:db8::7", True),
    ("source_ip", "2001:db8::8", True),
    ("source_ip", "2001:db8::9", True),
    ("source_ip", "2001:db8::a", True),
    ("source_ip", "2001:db8::b", True),
    ("source_ip", "2001:db8::c", True),
    ("source_ip", "2001:db8::d", True),
    ("source_ip", "2001:db8::e", True),
    ("source_ip", "2001:db8::f", True),
    ("source_ip", "2001:db8::10", True),
    ("source_ip", "2001:db8::11", True),
    ("source_ip", "2001:db8::12", True),
    ("source_ip", "2001:db8::13", True),
    ("source_ip", "2001:db8::14", True),
    ("source_ip", "", False),
    ("source_ip", " ", False),
    ("source_ip", "256.0.0.1", False),
    ("source_ip", "192.0.2", False),
    ("source_ip", "192.0.2.1.1", False),
    ("source_ip", "999.999.999.999", False),
    ("source_ip", "abc", False),
    ("source_ip", "localhost", False),
    ("source_ip", "::gg", False),
    ("source_ip", "2001:db8:::1", False),
    ("source_ip", "2001:db8::1/64", False),
    ("source_ip", "1.2.3.4:80", False),
    ("source_ip", "[2001:db8::1]", False),
    ("source_ip", "0x7f000001", False),
    ("source_ip", "192.0.2.-1", False),
    ("source_ip", "192.0.2.999", False),
    ("source_ip", "2001:db8::zz", False),
    ("source_ip", "192.168.1.1/24", False),
    ("source_ip", "fe80::1%", False),
    ("source_ip", "300.1.1.1", False),
    ("timestamp", "2026-01-01T00:00:00Z", True),
    ("timestamp", "2026-02-02T12:30:45+00:00", True),
    ("timestamp", "2026-03-03T08:15:00+05:30", True),
    ("timestamp", "2026-04-04T23:59:59-04:00", True),
    ("timestamp", "2026-05-05T00:00:01+01:00", True),
    ("timestamp", "2026-06-06T06:06:06-07:00", True),
    ("timestamp", "2026-07-07T07:07:07+09:00", True),
    ("timestamp", "2026-08-08T08:08:08+05:45", True),
    ("timestamp", "2026-09-09T09:09:09+03:30", True),
    ("timestamp", "2026-10-10T10:10:10-03:30", True),
    ("timestamp", "2026-01-01T00:00:00", False),
    ("timestamp", "not-a-date", False),
    ("timestamp", "2026-13-01T00:00:00Z", False),
    ("timestamp", "2026-01-32T00:00:00Z", False),
    ("timestamp", "2026-01-01 00:00:00", False),
    ("timestamp", "", False),
    ("timestamp", "2026-01-01", False),
    ("timestamp", "2026-01-01T25:00:00Z", False),
    ("timestamp", "2026-01-01T00:61:00Z", False),
    ("timestamp", "2026-01-01T00:00:00+99:99", False),
    ("username", "", False),
    ("username", " ", False),
    ("username", "\t", False),
    ("username", "\n", False),
    ("username", "\r", False),
    ("username", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", False),
    ("host", "", False),
    ("host", " ", False),
    ("host", "\t", False),
    ("host", "\n", False),
    ("host", "\u2003", False),
]


@pytest.mark.parametrize("field,value,valid", CASES)
def test_event_model_validation_matrix(field, value, valid):
    payload = {
        "timestamp": "2026-11-01T10:00:00Z",
        "event_type": "login_failure",
        "username": "lab-user",
        "source_ip": "192.0.2.10",
        "host": "lab-win01",
    }
    payload[field] = value
    if valid:
        event = SecurityEventIn.model_validate(payload)
        if field in {"username", "host"}:
            assert getattr(event, field) == value.strip()
        else:
            assert getattr(event, field) is not None
    else:
        with pytest.raises(ValidationError):
            SecurityEventIn.model_validate(payload)
