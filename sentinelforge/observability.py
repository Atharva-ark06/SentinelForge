"""Minimal JSON request logging without telemetry payloads or credentials."""

import json
import logging
import time
import uuid
from datetime import datetime, timezone

logger = logging.getLogger("sentinelforge.http")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


def new_request_id() -> str:
    return uuid.uuid4().hex


def log_request(*, request_id: str, method: str, path: str, status: int, duration_ms: float) -> None:
    logger.info(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": "http_request",
        "request_id": request_id,
        "method": method,
        "path": path,
        "status": status,
        "duration_ms": round(duration_ms, 2),
    }, separators=(",", ":")))


def monotonic_start() -> float:
    return time.monotonic()


def elapsed_ms(start: float) -> float:
    return (time.monotonic() - start) * 1000
