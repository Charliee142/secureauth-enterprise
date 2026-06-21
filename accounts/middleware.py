import time

from django.conf import settings
from django.contrib.auth import logout
from django.core.cache import cache
from django.http import HttpResponse


class SessionInactivityTimeoutMiddleware:
    """Enforces SEC-003: expire sessions after N seconds of inactivity."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_seen = request.session.get("_last_activity")
            now = time.time()
            timeout = settings.SESSION_INACTIVITY_TIMEOUT_SECONDS
            if last_seen and (now - last_seen) > timeout:
                logout(request)
            else:
                request.session["_last_activity"] = now
        return self.get_response(request)


class SimpleRateLimitMiddleware:
    """Enforces SEC-002: cache-based rate limiting on sensitive auth paths."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "POST" and any(
            request.path.startswith(p) for p in settings.RATE_LIMITED_PATH_PREFIXES
        ):
            ip = self._client_ip(request)
            key = f"ratelimit:{request.path}:{ip}"
            count = cache.get(key, 0)
            if count >= settings.RATE_LIMIT_MAX_REQUESTS:
                return HttpResponse(
                    "Too many requests. Please try again later.", status=429
                )
            cache.set(key, count + 1, timeout=settings.RATE_LIMIT_WINDOW_SECONDS)
        return self.get_response(request)

    @staticmethod
    def _client_ip(request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "0.0.0.0")
