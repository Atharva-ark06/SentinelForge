"""Regression tests for bounded client-identity retention."""

from sentinelforge.rate_limit import FixedWindowLimiter


def test_expired_client_identity_is_reclaimed_at_capacity():
    limiter = FixedWindowLimiter(limit=2, window_seconds=60, max_clients=1)
    assert limiter.allow("old-client", now=0)
    assert limiter.allow("new-client", now=61)
    assert "old-client" not in limiter._requests


def test_active_client_identity_still_exhausts_capacity():
    limiter = FixedWindowLimiter(limit=2, window_seconds=60, max_clients=1)
    assert limiter.allow("active-client", now=0)
    assert not limiter.allow("other-client", now=1)


def test_expired_same_client_window_resets():
    limiter = FixedWindowLimiter(limit=1, window_seconds=60, max_clients=1)
    assert limiter.allow("client", now=0)
    assert not limiter.allow("client", now=59)
    assert limiter.allow("client", now=60)
