"""Representative HTTP request log cases across status and endpoint combinations."""

import json
import logging
from io import StringIO

import pytest

from sentinelforge.observability import log_request, new_request_id


CASES = [
    ("POST", "/redoc", 204),
    ("GET", "/redoc", 204),
    ("PATCH", "/docs", 204),
    ("POST", "/docs", 204),
    ("GET", "/docs", 204),
    ("PATCH", "/metrics", 204),
    ("POST", "/metrics", 204),
    ("GET", "/metrics", 204),
    ("PATCH", "/alerts", 204),
    ("POST", "/alerts", 204),
    ("GET", "/alerts", 204),
    ("PATCH", "/events", 204),
    ("POST", "/events", 204),
    ("GET", "/events", 204),
    ("PATCH", "/health", 204),
    ("POST", "/health", 204),
    ("GET", "/health", 204),
    ("PATCH", "/redoc", 201),
    ("POST", "/redoc", 201),
    ("GET", "/redoc", 201),
    ("PATCH", "/docs", 201),
    ("POST", "/docs", 201),
    ("GET", "/docs", 201),
    ("PATCH", "/metrics", 201),
    ("POST", "/metrics", 201),
    ("GET", "/metrics", 201),
    ("PATCH", "/alerts", 201),
    ("POST", "/alerts", 201),
    ("GET", "/alerts", 201),
    ("PATCH", "/events", 201),
    ("POST", "/events", 201),
    ("GET", "/events", 201),
    ("PATCH", "/health", 201),
    ("POST", "/health", 201),
    ("GET", "/health", 201),
    ("PATCH","/redoc",404),
    ("POST","/redoc",403),
    ("GET","/redoc",401),
    ("PATCH","/docs",400),
    ("POST","/docs",204),
    ("GET","/docs",201),
    ("PATCH","/metrics",200),
    ("POST","/metrics",503),
    ("GET","/metrics",500),
    ("PATCH","/alerts",429),
    ("POST","/alerts",422),
    ("GET","/alerts",404),
    ("PATCH","/events",403),
    ("POST","/events",401),
    ("GET","/events",400),
    ("PATCH","/health",204),
    ("POST","/health",201),
    ("GET","/health",200),
]


@pytest.mark.parametrize("method,path,status", CASES)
def test_request_log_case(method, path, status):
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("sentinelforge.http")
    logger.addHandler(handler)
    try:
        log_request(request_id=new_request_id(), method=method, path=path, status=status, duration_ms=2.5)
    finally:
        logger.removeHandler(handler)
    data = json.loads(stream.getvalue())
    assert (data["method"], data["path"], data["status"]) == (method, path, status)
    assert data["duration_ms"] == 2.5
