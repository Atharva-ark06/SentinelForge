from datetime import datetime, timezone
from ipaddress import ip_address
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class SecurityEventIn(BaseModel):
    """Normalized event accepted by the ingestion API."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    event_type: Literal["login_success", "login_failure"]
    username: str = Field(min_length=1, max_length=128)
    source_ip: str = Field(min_length=1, max_length=64)
    host: str = Field(min_length=1, max_length=128)

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone, e.g. Z or +00:00")
        return value.astimezone(timezone.utc)

    @field_validator("username", "host")
    @classmethod
    def trim_nonempty_strings(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("value cannot be blank")
        return cleaned

    @field_validator("source_ip")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        try:
            return str(ip_address(value.strip()))
        except ValueError as exc:
            raise ValueError("source_ip must be a valid IPv4 or IPv6 address") from exc


class SecurityEvent(SecurityEventIn):
    id: int


class AlertOut(BaseModel):
    id: int
    rule_id: str
    title: str
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    evidence: list[int]
    source_ip: str
    username: str | None
    first_seen: datetime
    last_seen: datetime
