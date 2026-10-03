from app.ratelimit import RateLimiter


def test_sliding_window():
    now = [0.0]
    rl = RateLimiter(limit=2, window_seconds=60, clock=lambda: now[0])
    assert rl.check("a") is None
    assert rl.check("a") is None
    retry = rl.check("a")
    assert retry is not None and 0 < retry <= 60
    assert rl.check("b") is None  # other clients unaffected
    now[0] = 61
    assert rl.check("a") is None
