"""Security Core: limites locais e cabeçalhos defensivos (não substitui WAF distribuído)."""
import os
import threading
import time
from collections import defaultdict, deque
from fastapi.responses import JSONResponse

class SlidingWindowLimiter:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self._lock = threading.Lock()
        self._hits = defaultdict(deque)

    def allow(self, key, limit, seconds):
        now = self.clock()
        with self._lock:
            # Remove chaves antigas para limitar o consumo de memória.
            if len(self._hits) > 10000:
                for k, q in list(self._hits.items()):
                    if not q or now - q[-1] > 3600:
                        self._hits.pop(k, None)
            q = self._hits[key]
            while q and now - q[0] >= seconds:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True

limiter = SlidingWindowLimiter()
SENSITIVE = {
    '/auth/login': (8, 60),
    '/auth/register': (5, 3600),
    '/auth/register-first': (5, 3600),
    '/auth/password/request': (5, 3600),
    '/auth/password/confirm': (8, 3600),
}

async def security_middleware(request, call_next):
    path = request.url.path
    if request.method == 'OPTIONS':
        return await call_next(request)
    # Não confiar em X-Forwarded-For enviado pelo cliente. O proxy deve ser configurado à parte.
    ip = request.client.host if request.client else 'unknown'
    if path in SENSITIVE and request.method == 'POST':
        limit, period = SENSITIVE[path]
        if not limiter.allow((path, ip), limit, period):
            return JSONResponse({'detail': 'Muitas tentativas. Tente novamente mais tarde.'}, status_code=429, headers={'Retry-After': str(period)})
    response = await call_next(request)
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'DENY')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(self), camera=(self)')
    response.headers.setdefault('Cache-Control', 'no-store' if path.startswith('/auth/') else 'no-cache')
    if os.getenv('ASHLEY_FORCE_HTTPS', '0') == '1':
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response
