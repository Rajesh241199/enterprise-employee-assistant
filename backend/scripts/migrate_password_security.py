from sqlalchemy import text

from app.db.session import engine


CREATE_SECURITY_TABLE = text(
    """
    CREATE TABLE IF NOT EXISTS
    user_security_states (
        user_id INTEGER PRIMARY KEY
            REFERENCES users(id)
            ON DELETE CASCADE,

        must_change_password BOOLEAN
            NOT NULL
            DEFAULT FALSE,

        password_changed_at
            TIMESTAMP WITH TIME ZONE
            NULL,

        created_at
            TIMESTAMP WITH TIME ZONE
            NOT NULL
            DEFAULT NOW(),

        updated_at
            TIMESTAMP WITH TIME ZONE
            NOT NULL
            DEFAULT NOW()
    )
    """
)


BACKFILL_EXISTING_USERS = text(
    """
    INSERT INTO user_security_states (
        user_id,
        must_change_password,
        created_at,
        updated_at
    )
    SELECT
        users.id,
        FALSE,
        NOW(),
        NOW()
    FROM users
    ON CONFLICT (user_id)
    DO NOTHING
    """
)


CREATE_TRIGGER_FUNCTION = text(
    """
    CREATE OR REPLACE FUNCTION
    set_employee_password_change_required()
    RETURNS TRIGGER
    AS $$
    BEGIN
        IF TG_OP = 'INSERT' THEN
            IF NEW.role = 'employee' THEN
                INSERT INTO user_security_states (
                    user_id,
                    must_change_password,
                    created_at,
                    updated_at
                )
                VALUES (
                    NEW.id,
                    TRUE,
                    NOW(),
                    NOW()
                )
                ON CONFLICT (user_id)
                DO UPDATE SET
                    must_change_password = TRUE,
                    updated_at = NOW();
            ELSE
                INSERT INTO user_security_states (
                    user_id,
                    must_change_password,
                    created_at,
                    updated_at
                )
                VALUES (
                    NEW.id,
                    FALSE,
                    NOW(),
                    NOW()
                )
                ON CONFLICT (user_id)
                DO NOTHING;
            END IF;

            RETURN NEW;
        END IF;

        IF TG_OP = 'UPDATE'
           AND NEW.hashed_password
               IS DISTINCT FROM
               OLD.hashed_password
           AND NEW.role = 'employee'
        THEN
            INSERT INTO user_security_states (
                user_id,
                must_change_password,
                created_at,
                updated_at
            )
            VALUES (
                NEW.id,
                TRUE,
                NOW(),
                NOW()
            )
            ON CONFLICT (user_id)
            DO UPDATE SET
                must_change_password = TRUE,
                updated_at = NOW();
        END IF;

        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql
    """
)


DROP_EXISTING_TRIGGER = text(
    """
    DROP TRIGGER IF EXISTS
    employee_password_change_required_trigger
    ON users
    """
)


CREATE_TRIGGER = text(
    """
    CREATE TRIGGER
    employee_password_change_required_trigger
    AFTER INSERT OR UPDATE OF hashed_password
    ON users
    FOR EACH ROW
    EXECUTE FUNCTION
    set_employee_password_change_required()
    """
)


def migrate() -> None:
    print(
        "Creating password-security table..."
    )

    with engine.begin() as connection:
        connection.execute(
            CREATE_SECURITY_TABLE
        )

        result = connection.execute(
            BACKFILL_EXISTING_USERS
        )

        connection.execute(
            CREATE_TRIGGER_FUNCTION
        )

        connection.execute(
            DROP_EXISTING_TRIGGER
        )

        connection.execute(
            CREATE_TRIGGER
        )

    print(
        "Password-security migration "
        "completed successfully."
    )

    print(
        "Existing users backfilled:",
        result.rowcount,
    )

    print(
        "Existing users keep their current "
        "access. New employees and employees "
        "whose passwords are reset must change "
        "their password at the next login."
    )


if __name__ == "__main__":
    migrate()