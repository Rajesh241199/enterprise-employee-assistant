import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

from app.core.config import settings
from app.db.session import SessionLocal


LOGGER = logging.getLogger(__name__)

AUDIT_LOCK = threading.Lock()


SENSITIVE_KEYS = {
    "password",
    "current_password",
    "new_password",
    "confirm_password",
    "temporary_password",
    "new_temporary_password",
    "hashed_password",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "jwt",
    "jwt_secret_key",
    "api_key",
    "secret",
    "database_url",
    "private_key",
}


INSERT_AUDIT_LOG = text(
    """
    INSERT INTO audit_logs (
        event_timestamp,
        event_type,
        outcome,
        request_id,
        actor_user_id,
        actor_email,
        actor_role,
        client_ip,
        user_agent,
        resource_type,
        resource_id,
        metadata
    )
    VALUES (
        CAST(
            :event_timestamp
            AS TIMESTAMP WITH TIME ZONE
        ),
        :event_type,
        :outcome,
        :request_id,
        :actor_user_id,
        :actor_email,
        :actor_role,
        :client_ip,
        :user_agent,
        :resource_type,
        :resource_id,
        CAST(:metadata_json AS JSONB)
    )
    """
)


def utc_now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def mask_sensitive_data(
    value: Any,
) -> Any:
    if isinstance(value, dict):
        masked = {}

        for key, item in value.items():
            normalized_key = (
                str(key)
                .strip()
                .lower()
            )

            if normalized_key in SENSITIVE_KEYS:
                masked[key] = "***MASKED***"
            else:
                masked[key] = (
                    mask_sensitive_data(
                        item
                    )
                )

        return masked

    if isinstance(value, list):
        return [
            mask_sensitive_data(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            mask_sensitive_data(item)
            for item in value
        ]

    if (
        isinstance(value, str)
        and len(value) > 1000
    ):
        return (
            value[:1000]
            + "...[truncated]"
        )

    return value


def write_file_audit_record(
    safe_record: dict[str, Any],
) -> None:
    try:
        audit_path = Path(
            settings.app_audit_log_file
        )

        audit_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with AUDIT_LOCK:
            with audit_path.open(
                "a",
                encoding="utf-8",
            ) as file:
                file.write(
                    json.dumps(
                        safe_record,
                        ensure_ascii=False,
                        default=str,
                    )
                )

                file.write("\n")

    except Exception:
        LOGGER.exception(
            "Unable to write audit record "
            "to the audit file."
        )


def write_database_audit_record(
    safe_record: dict[str, Any],
) -> None:
    db = SessionLocal()

    try:
        actor = (
            safe_record.get("actor")
            or {}
        )

        client = (
            safe_record.get("client")
            or {}
        )

        resource = (
            safe_record.get("resource")
            or {}
        )

        metadata_json = json.dumps(
            safe_record.get("metadata")
            or {},
            ensure_ascii=False,
            default=str,
        )

        resource_id = resource.get(
            "id"
        )

        if resource_id is not None:
            resource_id = str(
                resource_id
            )

        db.execute(
            INSERT_AUDIT_LOG,
            {
                "event_timestamp":
                    safe_record[
                        "timestamp"
                    ],

                "event_type":
                    safe_record[
                        "event_type"
                    ],

                "outcome":
                    safe_record[
                        "outcome"
                    ],

                "request_id":
                    safe_record.get(
                        "request_id"
                    ),

                "actor_user_id":
                    actor.get(
                        "user_id"
                    ),

                "actor_email":
                    actor.get(
                        "email"
                    ),

                "actor_role":
                    actor.get(
                        "role"
                    ),

                "client_ip":
                    client.get(
                        "ip"
                    ),

                "user_agent":
                    client.get(
                        "user_agent"
                    ),

                "resource_type":
                    resource.get(
                        "type"
                    ),

                "resource_id":
                    resource_id,

                "metadata_json":
                    metadata_json,
            },
        )

        db.commit()

    except Exception:
        db.rollback()

        LOGGER.exception(
            "Unable to write audit record "
            "to PostgreSQL."
        )

    finally:
        db.close()


def write_audit_record(
    record: dict[str, Any],
) -> None:
    safe_record = mask_sensitive_data(
        record
    )

    write_file_audit_record(
        safe_record
    )

    write_database_audit_record(
        safe_record
    )


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
    resource_id:
        str | int | None = None,
    metadata:
        dict[str, Any] | None = None,
) -> None:
    record = {
        "timestamp":
            utc_now_iso(),

        "event_type":
            event_type,

        "outcome":
            outcome,

        "request_id":
            request_id,

        "actor": {
            "user_id":
                actor_user_id,

            "email":
                actor_email,

            "role":
                actor_role,
        },

        "client": {
            "ip":
                client_ip,

            "user_agent":
                user_agent,
        },

        "resource": {
            "type":
                resource_type,

            "id":
                resource_id,
        },

        "metadata":
            metadata or {},
    }

    write_audit_record(
        record
    )