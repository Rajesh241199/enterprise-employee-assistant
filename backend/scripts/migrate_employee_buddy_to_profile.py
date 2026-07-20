from sqlalchemy import text

from app.db.session import engine


ADD_BUDDY_NAME_COLUMN = text(
    """
    ALTER TABLE employee_onboarding_profiles
    ADD COLUMN IF NOT EXISTS
    buddy_name VARCHAR(150)
    """
)


ADD_BUDDY_EMAIL_COLUMN = text(
    """
    ALTER TABLE employee_onboarding_profiles
    ADD COLUMN IF NOT EXISTS
    buddy_email VARCHAR(255)
    """
)


BACKFILL_EXISTING_BUDDIES = text(
    """
    UPDATE employee_onboarding_profiles
    AS profile
    SET
        buddy_name = COALESCE(
            profile.buddy_name,
            mapping.buddy_name
        ),
        buddy_email = COALESCE(
            profile.buddy_email,
            mapping.buddy_email
        )
    FROM users AS employee
    JOIN departments AS department
      ON department.id
         = employee.department_id
    JOIN employee_poc_mapping AS mapping
      ON LOWER(mapping.department)
         = LOWER(department.name)
     AND LOWER(
            COALESCE(
                mapping.location,
                ''
            )
         )
         = LOWER(
            COALESCE(
                employee.location,
                ''
            )
         )
    WHERE profile.user_id = employee.id
      AND (
          profile.buddy_name IS NULL
          OR profile.buddy_email IS NULL
      )
    """
)


def migrate() -> None:
    print(
        "Adding employee-specific "
        "buddy columns..."
    )

    with engine.begin() as connection:
        connection.execute(
            ADD_BUDDY_NAME_COLUMN
        )

        connection.execute(
            ADD_BUDDY_EMAIL_COLUMN
        )

        result = connection.execute(
            BACKFILL_EXISTING_BUDDIES
        )

    print(
        "Employee buddy migration "
        "completed."
    )

    print(
        "Profiles backfilled:",
        result.rowcount,
    )


if __name__ == "__main__":
    migrate()