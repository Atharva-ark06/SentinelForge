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
