import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings


logger = logging.getLogger("app.errors")


def get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        if exc.status_code >= 500:
            logger.error(
                "HTTP exception occurred.",
                extra={
                    "event_name": "http.exception",
                    "request_id": get_request_id(request),
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": exc.status_code,
                    "error_type": exc.__class__.__name__,
                },
            )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "request_id": get_request_id(request),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        logger.warning(
            "Request validation failed.",
            extra={
                "event_name": "request.validation_failed",
                "request_id": get_request_id(request),
                "method": request.method,
                "path": request.url.path,
                "status_code": 422,
                "error_type": exc.__class__.__name__,
            },
        )

        content = {
            "detail": "Request validation failed.",
            "request_id": get_request_id(request),
        }

        if settings.app_debug:
            content["errors"] = exc.errors()

        return JSONResponse(
            status_code=422,
            content=content,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "Unhandled application exception.",
            extra={
                "event_name": "app.unhandled_exception",
                "request_id": get_request_id(request),
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "error_type": exc.__class__.__name__,
            },
        )

        content = {
            "detail": "Internal server error.",
            "request_id": get_request_id(request),
        }

        if settings.app_debug:
            content["error_type"] = exc.__class__.__name__
            content["error"] = str(exc)

        return JSONResponse(
            status_code=500,
            content=content,
        )