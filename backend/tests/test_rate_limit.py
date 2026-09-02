from app.core.rate_limit import SlidingWindowRateLimiter


def test_rate_limiter_blocks_requests_after_limit() -> None:
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=60)

    assert limiter.check("127.0.0.1").allowed is True
    assert limiter.check("127.0.0.1").allowed is True

    result = limiter.check("127.0.0.1")

    assert result.allowed is False
    assert result.retry_after_seconds > 0


def test_rate_limiter_keeps_clients_independent() -> None:
    limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60)

    assert limiter.check("client-a").allowed is True
    assert limiter.check("client-b").allowed is True
