"""Regression matrix for accepted IPv4 addresses at the Pydantic API boundary."""
import pytest
from sentinelforge.models import SecurityEventIn

VALID_IPS = [
    "192.0.2.1",    "192.0.2.2",    "192.0.2.3",    "192.0.2.4",    "192.0.2.5",    "192.0.2.6",    "192.0.2.7",    "192.0.2.8",    "192.0.2.9",    "192.0.2.10",    "192.0.2.11",    "192.0.2.12",    "192.0.2.13",    "192.0.2.14",    "192.0.2.15",    "192.0.2.16",    "192.0.2.17",
]

@pytest.mark.parametrize("source_ip", VALID_IPS)
def test_valid_ipv4_is_preserved(source_ip):
    event = SecurityEventIn(
        timestamp="2026-01-01T00:00:00Z",
        event_type="login_failure",
        username="lab-user",
        source_ip=source_ip,
        host="lab-host",
    )
    assert event.source_ip == source_ip
