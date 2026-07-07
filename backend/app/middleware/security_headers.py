import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds production-style security headers and request IDs.

    Headers added:
    - X-Request-ID
    - X-Content-Type-Options
    - X-Frame-Options
    - Referrer-Policy
    - Permissions-Policy
    - Cache-Control for API responses
    - Strict-Transport-Security in production
    """

    async def dispatch(self, request: Request, call_next):
        request_id = (
            getattr(request.state, "request_id", None)
            or request.headers.get("X-Request-ID")
            or str(uuid.uuid4())
        )
        request.state.request_id = request_id

        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=()",
        )

        if request.url.path.startswith("/api"):
            response.headers.setdefault(
                "Cache-Control",
                "no-store, no-cache, must-revalidate, max-age=0",
            )
            response.headers.setdefault("Pragma", "no-cache")

        if settings.app_env.lower() in {"prod", "production"}:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
            )

        return response