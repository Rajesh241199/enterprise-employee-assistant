import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import settings


AUDIT_LOCK = threading.Lock()


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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def mask_sensitive_data(value: Any) -> Any:
    if isinstance(value, dict):
        masked = {}

        for key, item in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                masked[key] = "***MASKED***"
            else:
                masked[key] = mask_sensitive_data(item)

        return masked

    if isinstance(value, list):
        return [mask_sensitive_data(item) for item in value]

    if isinstance(value, str) and len(value) > 1000:
        return value[:1000] + "...[truncated]"

    return value


def write_audit_record(record: dict[str, Any]) -> None:
    audit_path = Path(settings.app_audit_log_file)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    safe_record = mask_sensitive_data(record)

    with AUDIT_LOCK:
        with audit_path.open("a", encoding="utf-8") as file:
            file.write(
                json.dumps(
                    safe_record,
                    ensure_ascii=False,
                    default=str,
                )
            )
            file.write("\n")


def audit_event(
    event_type: str,
    outcome: str,
    request_id: str | None = None,
    actor_user_id: int | None = None,
    actor_email: str | None = None,
    actor_role: str | None = None,
    client_ip: str | None = None,
    user_agent: str | None = None,
    resource_type: str | None = None,
    resource_id: str | int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    record = {
        "timestamp": utc_now_iso(),
        "event_type": event_type,
        "outcome": outcome,
        "request_id": request_id,
        "actor": {
            "user_id": actor_user_id,
            "email": actor_email,
            "role": actor_role,
        },
        "client": {
            "ip": client_ip,
            "user_agent": user_agent,
        },
        "resource": {
            "type": resource_type,
            "id": resource_id,
        },
        "metadata": metadata or {},
    }

    write_audit_record(record)