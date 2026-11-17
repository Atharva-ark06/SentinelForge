from sentinelforge.rate_limit import FixedWindowLimiter



def test_limiter_blocks_at_capacity():
    limiter = FixedWindowLimiter(limit=2)
    assert limiter.allow("client", now=1)
    assert limiter.allow("client", now=2)
    assert not limiter.allow("client", now=3)


def test_limiter_reopens_after_window():
    limiter = FixedWindowLimiter(limit=1, window_seconds=10)
    assert limiter.allow("client", now=1)
    assert not limiter.allow("client", now=2)
    assert limiter.allow("client", now=11)


def test_limiter_isolates_clients():
    limiter = FixedWindowLimiter(limit=1)
    assert limiter.allow("first", now=1)
    assert limiter.allow("second", now=1)


def test_limiter_fails_closed_when_client_capacity_reached():
    limiter = FixedWindowLimiter(limit=1, max_clients=1)
    assert limiter.allow("first", now=1)
    assert not limiter.allow("second", now=1)
