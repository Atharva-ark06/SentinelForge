"""Representative HTTP request log cases across status and endpoint combinations."""

import json
import logging
from io import StringIO

import pytest

from sentinelforge.observability import log_request, new_request_id


CASES = [
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
