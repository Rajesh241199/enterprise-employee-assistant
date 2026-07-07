import json
import logging
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from app.core.config import settings


SENSITIVE_KEYS = {
    "password",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "jwt",
    "jwt_secret_key",
    "api_key",
    "secret",
    "database_url",
}


EXTRA_LOG_FIELDS = [
    "event_name",
    "request_id",
    "method",
    "path",
    "status_code",
    "duration_ms",
    "client_ip",
    "user_agent",
    "error_type",
    "route",
    "user_id",
    "email",
    "role",
    "resource_type",
    "resource_id",
    "outcome",
]


def mask_sensitive_value(key: str, value: Any) -> Any:
    if key.lower() in SENSITIVE_KEYS:
        return "***MASKED***"

    if isinstance(value, str) and len(value) > 500:
        return value[:500] + "...[truncated]"

    return value


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record: dict[str, Any] = {
            "timestamp": utc_now_iso(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": settings.app_env,
            "service": settings.app_name,
        }

        for field in EXTRA_LOG_FIELDS:
            if hasattr(record, field):
                value = getattr(record, field)
                log_record[field] = mask_sensitive_value(field, value)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(
            log_record,
            ensure_ascii=False,
            default=str,
        )


def ensure_log_directories() -> None:
    Path(settings.app_log_dir).mkdir(parents=True, exist_ok=True)

    for log_file in [
        settings.app_log_file,
        settings.app_error_log_file,
        settings.app_audit_log_file,
    ]:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)


def build_file_handler(
    file_path: str,
    level: int,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        filename=file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(JsonLogFormatter())

    return handler


def build_console_handler() -> logging.StreamHandler:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    handler.setFormatter(JsonLogFormatter())

    return handler


def setup_logging() -> None:
    ensure_log_directories()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    app_file_handler = build_file_handler(
        file_path=settings.app_log_file,
        level=logging.INFO,
    )

    error_file_handler = build_file_handler(
        file_path=settings.app_error_log_file,
        level=logging.ERROR,
    )

    console_handler = build_console_handler()

    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_file_handler)
    root_logger.addHandler(error_file_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)

    logging.getLogger("app.startup").info(
        "Logging configured.",
        extra={
            "event_name": "logging.configured",
        },
    )