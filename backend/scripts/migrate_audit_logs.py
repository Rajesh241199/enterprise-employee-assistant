from sqlalchemy import text

from app.db.session import engine


CREATE_AUDIT_LOGS_TABLE = text(
    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id BIGSERIAL PRIMARY KEY,

        event_timestamp
            TIMESTAMP WITH TIME ZONE
            NOT NULL,

        event_type VARCHAR(150)
            NOT NULL,

        outcome VARCHAR(50)
            NOT NULL,

        request_id VARCHAR(150)
            NULL,

        actor_user_id INTEGER
            NULL,

        actor_email VARCHAR(255)
            NULL,

        actor_role VARCHAR(50)
            NULL,

        client_ip VARCHAR(100)
            NULL,

        user_agent TEXT
            NULL,

        resource_type VARCHAR(100)
            NULL,

        resource_id VARCHAR(255)
            NULL,

        metadata JSONB
            NOT NULL
            DEFAULT '{}'::jsonb,

        created_at
            TIMESTAMP WITH TIME ZONE
            NOT NULL
            DEFAULT NOW()
    )
    """
)


CREATE_TIMESTAMP_INDEX = text(
    """
    CREATE INDEX IF NOT EXISTS
    ix_audit_logs_event_timestamp
    ON audit_logs (
        event_timestamp DESC
    )
    """
)


CREATE_EVENT_TYPE_INDEX = text(
    """
    CREATE INDEX IF NOT EXISTS
    ix_audit_logs_event_type
    ON audit_logs (
        event_type
    )
    """
)


CREATE_OUTCOME_INDEX = text(
    """
    CREATE INDEX IF NOT EXISTS
    ix_audit_logs_outcome
    ON audit_logs (
        outcome
    )
    """
)


CREATE_ACTOR_EMAIL_INDEX = text(
    """
    CREATE INDEX IF NOT EXISTS
    ix_audit_logs_actor_email
    ON audit_logs (
        actor_email
    )
    """
)


CREATE_ACTOR_ROLE_INDEX = text(
    """
    CREATE INDEX IF NOT EXISTS
    ix_audit_logs_actor_role
    ON audit_logs (
        actor_role
    )
    """
)


CREATE_RESOURCE_INDEX = text(
    """
    CREATE INDEX IF NOT EXISTS
    ix_audit_logs_resource
    ON audit_logs (
        resource_type,
        resource_id
    )
    """
)


def migrate() -> None:
    print(
        "Creating persistent audit-log table..."
    )

    statements = [
        CREATE_AUDIT_LOGS_TABLE,
        CREATE_TIMESTAMP_INDEX,
        CREATE_EVENT_TYPE_INDEX,
        CREATE_OUTCOME_INDEX,
        CREATE_ACTOR_EMAIL_INDEX,
        CREATE_ACTOR_ROLE_INDEX,
        CREATE_RESOURCE_INDEX,
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(statement)

    print(
        "Audit-log migration completed "
        "successfully."
    )


if __name__ == "__main__":
    migrate()