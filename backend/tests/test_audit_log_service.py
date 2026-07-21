from datetime import (
    datetime,
    timezone,
)

from app.services.audit_log_service import (
    row_to_audit_item,
)


def test_database_row_maps_to_audit_item():
    event_time = datetime.now(
        timezone.utc
    )

    row = {
        "id": 100,
        "event_timestamp":
            event_time,

        "event_type":
            "admin.onboarding."
            "employee_updated",

        "outcome":
            "success",

        "request_id":
            "request-100",

        "actor_user_id":
            2,

        "actor_email":
            "priya.hr@company.com",

        "actor_role":
            "hr_admin",

        "client_ip":
            "127.0.0.1",

        "user_agent":
            "pytest",

        "resource_type":
            (
                "employee_"
                "onboarding_profile"
            ),

        "resource_id":
            "6",

        "metadata": {
            "employee_id":
                "EMP006",
        },
    }

    result = row_to_audit_item(
        row
    )

    assert result.id == 100

    assert (
        result.timestamp
        == event_time
    )

    assert result.actor.email == (
        "priya.hr@company.com"
    )

    assert result.actor.role == (
        "hr_admin"
    )

    assert result.resource.id == (
        "6"
    )

    assert (
        result.metadata[
            "employee_id"
        ]
        == "EMP006"
    )


def test_invalid_metadata_becomes_empty_object():
    row = {
        "id": 101,
        "event_timestamp":
            datetime.now(
                timezone.utc
            ),

        "event_type":
            "auth.login_success",

        "outcome":
            "success",

        "request_id":
            None,

        "actor_user_id":
            None,

        "actor_email":
            None,

        "actor_role":
            None,

        "client_ip":
            None,

        "user_agent":
            None,

        "resource_type":
            "auth",

        "resource_id":
            None,

        "metadata":
            "invalid-metadata",
    }

    result = row_to_audit_item(
        row
    )

    assert result.metadata == {}