import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import settings


logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every API request as structured JSON.

    Captures:
    - request_id
    - method
    - path
    - status code
    - duration
    - client IP
    - user agent
    - slow request signal
    """

    def __init__(
        self,
        app,
        slow_request_threshold_ms: int | None = None,
    ):
        super().__init__(app)
        self.slow_request_threshold_ms = (
            slow_request_threshold_ms or settings.slow_request_threshold_ms
        )

    def get_request_id(self, request: Request) -> str:
        existing_request_id = getattr(request.state, "request_id", None)

        if existing_request_id:
            return existing_request_id

        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        return request_id

    def get_client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")

        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        if request.client:
            return request.client.host

        return "unknown"

    async def dispatch(self, request: Request, call_next):
        request_id = self.get_request_id(request)
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")

        start_time = time.perf_counter()
        status_code = 500
        error_type = None

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response

        except Exception as exc:
            error_type = exc.__class__.__name__
            raise

        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            is_slow_request = duration_ms >= self.slow_request_threshold_ms
            is_error_response = status_code >= 500

            level = logging.INFO

            if is_error_response or is_slow_request:
                level = logging.WARNING

            logger.log(
                level,
                "HTTP request completed.",
                extra={
                    "event_name": "http.request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                    "user_agent": user_agent,
                    "error_type": error_type,
                },
            )