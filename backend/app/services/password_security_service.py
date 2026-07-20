from sqlalchemy import text
from sqlalchemy.orm import Session


GET_PASSWORD_STATE = text(
    """
    SELECT
        must_change_password,
        password_changed_at
    FROM user_security_states
    WHERE user_id = :user_id
    """
)


UPSERT_PASSWORD_CHANGE_REQUIRED = text(
    """
    INSERT INTO user_security_states (
        user_id,
        must_change_password,
        created_at,
        updated_at
    )
    VALUES (
        :user_id,
        TRUE,
        NOW(),
        NOW()
    )
    ON CONFLICT (user_id)
    DO UPDATE SET
        must_change_password = TRUE,
        updated_at = NOW()
    """
)


UPSERT_PASSWORD_CHANGED = text(
    """
    INSERT INTO user_security_states (
        user_id,
        must_change_password,
        password_changed_at,
        created_at,
        updated_at
    )
    VALUES (
        :user_id,
        FALSE,
        NOW(),
        NOW(),
        NOW()
    )
    ON CONFLICT (user_id)
    DO UPDATE SET
        must_change_password = FALSE,
        password_changed_at = NOW(),
        updated_at = NOW()
    """
)


def is_password_change_required(
    db: Session,
    user_id: int,
) -> bool:
    row = db.execute(
        GET_PASSWORD_STATE,
        {
            "user_id": user_id,
        },
    ).mappings().first()

    if not row:
        return False

    return bool(
        row["must_change_password"]
    )


def mark_password_change_required(
    db: Session,
    user_id: int,
) -> None:
    db.execute(
        UPSERT_PASSWORD_CHANGE_REQUIRED,
        {
            "user_id": user_id,
        },
    )


def mark_password_changed(
    db: Session,
    user_id: int,
) -> None:
    db.execute(
        UPSERT_PASSWORD_CHANGED,
        {
            "user_id": user_id,
        },
    )