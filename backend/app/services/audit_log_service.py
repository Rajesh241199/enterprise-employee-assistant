from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.audit import (
    AuditActor,
    AuditClient,
    AuditLogItem,
    AuditLogListResponse,
    AuditLogSummaryResponse,
    AuditResource,
)


SUMMARY_QUERY = text(
    """
    SELECT
        COUNT(*) AS total_events,

        COUNT(*) FILTER (
            WHERE LOWER(outcome)
                  = 'success'
        ) AS successful_events,

        COUNT(*) FILTER (
            WHERE LOWER(outcome)
                  = 'failure'
        ) AS failed_events,

        COUNT(*) FILTER (
            WHERE LOWER(outcome)
                  = 'blocked'
        ) AS blocked_events,

        COUNT(*) FILTER (
            WHERE event_timestamp
                  >= NOW()
                  - INTERVAL '24 hours'
        ) AS events_last_24_hours

    FROM audit_logs
    """
)


def build_filter_conditions(
    event_type: str | None,
    outcome: str | None,
    actor_email: str | None,
    actor_role: str | None,
    resource_type: str | None,
    start_time: datetime | None,
    end_time: datetime | None,
) -> tuple[list[str], dict]:
    conditions = [
        "1 = 1",
    ]

    parameters: dict = {}

    if event_type:
        conditions.append(
            """
            event_type ILIKE
            :event_type
            """
        )

        parameters["event_type"] = (
            f"%{event_type.strip()}%"
        )

    if outcome:
        conditions.append(
            """
            LOWER(outcome)
            = LOWER(:outcome)
            """
        )

        parameters["outcome"] = (
            outcome.strip()
        )

    if actor_email:
        conditions.append(
            """
            actor_email ILIKE
            :actor_email
            """
        )

        parameters["actor_email"] = (
            f"%{actor_email.strip()}%"
        )

    if actor_role:
        conditions.append(
            """
            LOWER(actor_role)
            = LOWER(:actor_role)
            """
        )

        parameters["actor_role"] = (
            actor_role.strip()
        )

    if resource_type:
        conditions.append(
            """
            resource_type ILIKE
            :resource_type
            """
        )

        parameters[
            "resource_type"
        ] = (
            f"%{resource_type.strip()}%"
        )

    if start_time:
        conditions.append(
            """
            event_timestamp
            >= :start_time
            """
        )

        parameters["start_time"] = (
            start_time
        )

    if end_time:
        conditions.append(
            """
            event_timestamp
            <= :end_time
            """
        )

        parameters["end_time"] = (
            end_time
        )

    return conditions, parameters


def row_to_audit_item(
    row,
) -> AuditLogItem:
    metadata = row["metadata"]

    if not isinstance(
        metadata,
        dict,
    ):
        metadata = {}

    return AuditLogItem(
        id=row["id"],

        timestamp=(
            row["event_timestamp"]
        ),

        event_type=(
            row["event_type"]
        ),

        outcome=(
            row["outcome"]
        ),

        request_id=(
            row["request_id"]
        ),

        actor=AuditActor(
            user_id=(
                row["actor_user_id"]
            ),

            email=(
                row["actor_email"]
            ),

            role=(
                row["actor_role"]
            ),
        ),

        client=AuditClient(
            ip=row["client_ip"],

            user_agent=(
                row["user_agent"]
            ),
        ),

        resource=AuditResource(
            type=(
                row["resource_type"]
            ),

            id=(
                row["resource_id"]
            ),
        ),

        metadata=metadata,
    )


def list_audit_logs(
    db: Session,
    offset: int,
    limit: int,
    event_type: str | None = None,
    outcome: str | None = None,
    actor_email: str | None = None,
    actor_role: str | None = None,
    resource_type: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
) -> AuditLogListResponse:
    conditions, parameters = (
        build_filter_conditions(
            event_type=event_type,
            outcome=outcome,
            actor_email=actor_email,
            actor_role=actor_role,
            resource_type=(
                resource_type
            ),
            start_time=start_time,
            end_time=end_time,
        )
    )

    where_clause = " AND ".join(
        conditions
    )

    total_query = text(
        f"""
        SELECT COUNT(*) AS total
        FROM audit_logs
        WHERE {where_clause}
        """
    )

    data_query = text(
        f"""
        SELECT
            id,
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

        FROM audit_logs

        WHERE {where_clause}

        ORDER BY
            event_timestamp DESC,
            id DESC

        OFFSET :offset
        LIMIT :limit
        """
    )

    total_row = db.execute(
        total_query,
        parameters,
    ).mappings().first()

    data_parameters = {
        **parameters,
        "offset": offset,
        "limit": limit,
    }

    rows = db.execute(
        data_query,
        data_parameters,
    ).mappings().all()

    items = [
        row_to_audit_item(row)
        for row in rows
    ]

    return AuditLogListResponse(
        items=items,

        total=int(
            total_row["total"]
            if total_row
            else 0
        ),

        offset=offset,
        limit=limit,
    )


def get_audit_log_summary(
    db: Session,
) -> AuditLogSummaryResponse:
    row = db.execute(
        SUMMARY_QUERY
    ).mappings().first()

    if not row:
        return AuditLogSummaryResponse(
            total_events=0,
            successful_events=0,
            failed_events=0,
            blocked_events=0,
            events_last_24_hours=0,
        )

    return AuditLogSummaryResponse(
        total_events=int(
            row["total_events"]
            or 0
        ),

        successful_events=int(
            row["successful_events"]
            or 0
        ),

        failed_events=int(
            row["failed_events"]
            or 0
        ),

        blocked_events=int(
            row["blocked_events"]
            or 0
        ),

        events_last_24_hours=int(
            row[
                "events_last_24_hours"
            ]
            or 0
        ),
    )