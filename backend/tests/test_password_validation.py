import pytest
from pydantic import ValidationError

from app.schemas.user import (
    ChangePasswordRequest,
    validate_secure_password,
)


@pytest.mark.parametrize(
    (
        "password",
        "expected_message",
    ),
    [
        (
            "Short@1",
            (
                "Password must contain "
                "at least 12 characters."
            ),
        ),
        (
            "lowercaseonly@2026",
            (
                "Password must contain "
                "at least one uppercase "
                "letter."
            ),
        ),
        (
            "UPPERCASEONLY@2026",
            (
                "Password must contain "
                "at least one lowercase "
                "letter."
            ),
        ),
        (
            "NoNumbersHere@",
            (
                "Password must contain "
                "at least one number."
            ),
        ),
        (
            "NoSpecialCharacter2026",
            (
                "Password must contain "
                "at least one special "
                "character."
            ),
        ),
    ],
)
def test_insecure_password_is_rejected(
    password: str,
    expected_message: str,
):
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        validate_secure_password(
            password
        )


def test_secure_password_is_accepted():
    password = (
        "SecurePassword@2026"
    )

    assert (
        validate_secure_password(
            password
        )
        == password
    )


def test_password_confirmation_must_match():
    with pytest.raises(
        ValidationError
    ) as error:
        ChangePasswordRequest(
            current_password=(
                "TemporaryPassword@2026"
            ),
            new_password=(
                "PermanentPassword@2026"
            ),
            confirm_password=(
                "DifferentPassword@2026"
            ),
        )

    assert (
        "do not match"
        in str(error.value)
    )


def test_new_password_must_differ():
    password = (
        "SecurePassword@2026"
    )

    with pytest.raises(
        ValidationError
    ) as error:
        ChangePasswordRequest(
            current_password=password,
            new_password=password,
            confirm_password=password,
        )

    assert (
        "must be different"
        in str(error.value)
    )


def test_valid_change_password_request():
    request = ChangePasswordRequest(
        current_password=(
            "TemporaryPassword@2026"
        ),
        new_password=(
            "PermanentPassword@2026"
        ),
        confirm_password=(
            "PermanentPassword@2026"
        ),
    )

    assert request.new_password == (
        "PermanentPassword@2026"
    )