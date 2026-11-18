"""Parameterized operational boundary cases for request IDs and safe log fields."""

import json
import logging
from io import StringIO

import pytest

from sentinelforge.observability import log_request, new_request_id


@pytest.mark.parametrize("status", [200, 201, 204, 301, 304, 400, 401, 403, 404, 409, 422, 429, 500, 502, 503, 504])
def test_json_log_status(status):
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("sentinelforge.http")
    logger.addHandler(handler)
    try:
        log_request(request_id=new_request_id(), method="GET", path="/health", status=status, duration_ms=0)
    finally:
        logger.removeHandler(handler)
    payload = json.loads(stream.getvalue())
    assert payload["status"] == status
    assert len(payload["request_id"]) == 32


@pytest.mark.parametrize("path", ["/health", "/docs", "/redoc", "/events", "/alerts", "/metrics"])
def test_json_log_paths(path):
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    logger = logging.getLogger("sentinelforge.http")
    logger.addHandler(handler)
    try:
        log_request(request_id=new_request_id(), method="GET", path=path, status=200, duration_ms=0)
    finally:
        logger.removeHandler(handler)
    assert json.loads(stream.getvalue())["path"] == path
