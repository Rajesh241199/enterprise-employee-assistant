from app.services import (
    audit_logger,
)


def test_sensitive_values_are_masked():
    input_data = {
        "email":
            "employee@company.com",

        "password":
            "SecretPassword@2026",

        "new_password":
            "NewSecretPassword@2026",

        "access_token":
            "secret-jwt-token",

        "metadata": {
            "temporary_password":
                "TemporaryPassword@2026",

            "safe_value":
                "visible",
        },
    }

    result = (
        audit_logger
        .mask_sensitive_data(
            input_data
        )
    )

    assert result["email"] == (
        "employee@company.com"
    )

    assert result["password"] == (
        "***MASKED***"
    )

    assert result["new_password"] == (
        "***MASKED***"
    )

    assert result["access_token"] == (
        "***MASKED***"
    )

    assert (
        result["metadata"]
        ["temporary_password"]
        == "***MASKED***"
    )

    assert (
        result["metadata"]
        ["safe_value"]
        == "visible"
    )


def test_sensitive_values_inside_lists_are_masked():
    input_data = [
        {
            "password":
                "Password@2026",
        },
        {
            "name":
                "Rajesh Kannan",
        },
    ]

    result = (
        audit_logger
        .mask_sensitive_data(
            input_data
        )
    )

    assert (
        result[0]["password"]
        == "***MASKED***"
    )

    assert (
        result[1]["name"]
        == "Rajesh Kannan"
    )


def test_long_text_is_truncated():
    long_value = "a" * 1200

    result = (
        audit_logger
        .mask_sensitive_data(
            long_value
        )
    )

    assert len(result) < len(
        long_value
    )

    assert result.endswith(
        "...[truncated]"
    )


def test_audit_event_builds_expected_record(
    monkeypatch,
):
    captured_records = []

    def capture_record(
        record,
    ):
        captured_records.append(
            record
        )

    monkeypatch.setattr(
        audit_logger,
        "write_audit_record",
        capture_record,
    )

    audit_logger.audit_event(
        event_type=(
            "auth.login_success"
        ),
        outcome="success",
        request_id="request-123",
        actor_user_id=10,
        actor_email=(
            "employee@company.com"
        ),
        actor_role="employee",
        client_ip="127.0.0.1",
        user_agent="pytest",
        resource_type="auth",
        resource_id="10",
        metadata={
            "employee_id":
                "EMP010",
        },
    )

    assert len(
        captured_records
    ) == 1

    record = captured_records[0]

    assert record["event_type"] == (
        "auth.login_success"
    )

    assert record["outcome"] == (
        "success"
    )

    assert record["actor"]["email"] == (
        "employee@company.com"
    )

    assert (
        record["resource"]["type"]
        == "auth"
    )

    assert (
        record["metadata"]
        ["employee_id"]
        == "EMP010"
    )