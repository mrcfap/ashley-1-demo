from app.security.security_core import SlidingWindowLimiter, SENSITIVE

def test_login_limit_and_expiration():
    now = [0.0]
    limiter = SlidingWindowLimiter(clock=lambda: now[0])
    for _ in range(8):
        assert limiter.allow(('login','client'), 8, 60)
    assert not limiter.allow(('login','client'), 8, 60)
    now[0] = 61
    assert limiter.allow(('login','client'), 8, 60)

def test_clients_are_isolated():
    limiter = SlidingWindowLimiter()
    assert limiter.allow(('login','a'), 1, 60)
    assert not limiter.allow(('login','a'), 1, 60)
    assert limiter.allow(('login','b'), 1, 60)

def test_sensitive_endpoints_covered():
    assert {'/auth/login','/auth/register','/auth/password/request','/auth/password/confirm'} <= set(SENSITIVE)
