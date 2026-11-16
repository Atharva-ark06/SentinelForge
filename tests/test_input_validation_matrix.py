"""Regression matrix for normalized event input validation."""
import pytest
from pydantic import ValidationError
from sentinelforge.models import SecurityEventIn

CASES = [
    ("source_ip", "192.0.2.1", true),
    ("source_ip", "192.0.2.2", true),
    ("source_ip", "192.0.2.3", true),
    ("source_ip", "192.0.2.4", true),
    ("source_ip", "192.0.2.5", true),
    ("source_ip", "192.0.2.6", true),
    ("source_ip", "192.0.2.7", true),
    ("source_ip", "192.0.2.8", true),
    ("source_ip", "192.0.2.9", true),
    ("source_ip", "192.0.2.10", true),
    ("source_ip", "192.0.2.11", true),
    ("source_ip", "192.0.2.12", true),
    ("source_ip", "192.0.2.13", true),
    ("source_ip", "192.0.2.14", true),
    ("source_ip", "192.0.2.15", true),
    ("source_ip", "192.0.2.16", true),
    ("source_ip", "192.0.2.17", true),
    ("source_ip", "192.0.2.18", true),
    ("source_ip", "192.0.2.19", true),
    ("source_ip", "192.0.2.20", true),
    ("source_ip", "2001:db8::1", true),
    ("source_ip", "2001:db8::2", true),
    ("source_ip", "2001:db8::3", true),
    ("source_ip", "2001:db8::4", true),
    ("source_ip", "2001:db8::5", true),
