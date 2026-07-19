import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import (
    HTTPException as StarletteHTTPException,
)

from app.core.config import settings


logger = logging.getLogger("app.errors")


def get_request_id(request: Request) -> str | None:
    return getattr(
        request.state,
        "request_id",
        None,
    )


def serialize_validation_errors(
    exc: RequestValidationError,
) -> list[dict[str, Any]]:
    """
    Convert Pydantic validation errors into JSON-safe objects.

    Raw input values are intentionally excluded because they may
    contain salary, rent, deduction, password or other private data.
    """
    safe_errors: list[dict[str, Any]] = []

    for error in exc.errors():
        safe_error: dict[str, Any] = {
            "type": str(
                error.get(
                    "type",
                    "validation_error",
                )
            ),
            "loc": list(error.get("loc", [])),
            "msg": str(
                error.get(
                    "msg",
                    "Invalid request value.",
                )
            ),
        }

        context = error.get("ctx")

        if isinstance(context, dict):
            safe_error["ctx"] = {
                str(key): str(value)
                for key, value in context.items()
            }

        safe_errors.append(safe_error)

    return safe_errors


def register_exception_handlers(
    app: FastAPI,
) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ):
        if exc.status_code >= 500:
            logger.error(
                "HTTP exception occurred.",
                extra={
                    "event_name": "http.exception",
                    "request_id": get_request_id(
                        request
                    ),
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": exc.status_code,
                    "error_type": (
                        exc.__class__.__name__
                    ),
                },
            )

        detail = exc.detail

        if isinstance(detail, Exception):
            detail = str(detail)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": detail,
                "request_id": get_request_id(
                    request
                ),
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
                "event_name": (
                    "request.validation_failed"
                ),
                "request_id": get_request_id(
                    request
                ),
                "method": request.method,
                "path": request.url.path,
                "status_code": 422,
                "error_type": (
                    exc.__class__.__name__
                ),
            },
        )

        content: dict[str, Any] = {
            "detail": "Request validation failed.",
            "request_id": get_request_id(
                request
            ),
        }

        if settings.app_debug:
            content["errors"] = (
                serialize_validation_errors(exc)
            )

        return JSONResponse(
            status_code=422,
            content=content,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ):
        logger.exception(
            "Unhandled application exception.",
            extra={
                "event_name": (
                    "app.unhandled_exception"
                ),
                "request_id": get_request_id(
                    request
                ),
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "error_type": (
                    exc.__class__.__name__
                ),
            },
        )

        content: dict[str, Any] = {
            "detail": "Internal server error.",
            "request_id": get_request_id(
                request
            ),
        }

        if settings.app_debug:
            content["error_type"] = (
                exc.__class__.__name__
            )
            content["error"] = str(exc)

        return JSONResponse(
            status_code=500,
            content=content,
        )