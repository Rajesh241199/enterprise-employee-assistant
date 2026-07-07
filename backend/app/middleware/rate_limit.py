import time
from collections import defaultdict, deque
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiter for local/demo production hardening.

    Protects:
    - brute-force login attempts
    - repeated expensive RAG calls
    - large request bodies
    - basic API abuse

    Note:
    For multi-instance cloud deployment, replace this with Redis-backed rate limiting.
    """

    def __init__(
        self,
        app,
        default_limit: int | None = None,
        default_window_seconds: int | None = None,
        login_limit: int | None = None,
        login_window_seconds: int | None = None,
        max_request_body_bytes: int | None = None,
    ):
        super().__init__(app)
        self.default_limit = default_limit or settings.rate_limit_requests
        self.default_window_seconds = (
            default_window_seconds or settings.rate_limit_window_seconds
        )
        self.login_limit = login_limit or settings.login_rate_limit_requests
        self.login_window_seconds = (
            login_window_seconds or settings.login_rate_limit_window_seconds
        )
        self.max_request_body_bytes = (
            max_request_body_bytes or settings.max_request_body_bytes
        )

        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        if request.client:
            return request.client.host

        return "unknown"

    def _is_exempt_path(self, path: str) -> bool:
        exempt_paths = {
            "/",
            "/health",
            "/ready",
            "/docs",
            "/redoc",
            "/openapi.json",
        }

        return path in exempt_paths

    def _limit_for_path(self, path: str) -> tuple[int, int]:
        if path == "/api/auth/login":
            return self.login_limit, self.login_window_seconds

        return self.default_limit, self.default_window_seconds

    def _build_key(self, request: Request) -> str:
        client_ip = self._get_client_ip(request)
        path = request.url.path

        if path == "/api/auth/login":
            return f"login:{client_ip}"

        return f"default:{client_ip}:{path}"

    def _is_allowed(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            bucket = self._requests[key]

            while bucket and bucket[0] < window_start:
                bucket.popleft()

            if len(bucket) >= limit:
                oldest = bucket[0]
                retry_after = max(1, int(window_seconds - (now - oldest)))
                return False, retry_after

            bucket.append(now)
            return True, 0

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if request.method == "OPTIONS" or self._is_exempt_path(path):
            return await call_next(request)

        content_length = request.headers.get("content-length")

        if content_length:
            try:
                body_size = int(content_length)

                if body_size > self.max_request_body_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": "Request body too large.",
                            "max_request_body_bytes": self.max_request_body_bytes,
                        },
                    )

            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "Invalid Content-Length header.",
                    },
                )

        limit, window_seconds = self._limit_for_path(path)
        key = self._build_key(request)

        allowed, retry_after = self._is_allowed(
            key=key,
            limit=limit,
            window_seconds=window_seconds,
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                headers={
                    "Retry-After": str(retry_after),
                },
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after_seconds": retry_after,
                },
            )

        return await call_next(request)