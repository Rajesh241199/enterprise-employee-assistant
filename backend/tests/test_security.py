from datetime import timedelta

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_is_not_plain_text():
    plain_password = (
        "SecurePassword@2026"
    )

    hashed_password = hash_password(
        plain_password
    )

    assert hashed_password
    assert hashed_password != plain_password


def test_correct_password_is_verified():
    plain_password = (
        "SecurePassword@2026"
    )

    hashed_password = hash_password(
        plain_password
    )

    assert verify_password(
        plain_password,
        hashed_password,
    )


def test_incorrect_password_is_rejected():
    hashed_password = hash_password(
        "SecurePassword@2026"
    )

    assert not verify_password(
        "IncorrectPassword@2026",
        hashed_password,
    )


def test_access_token_contains_subject():
    subject = (
        "employee@company.com"
    )

    token = create_access_token(
        subject=subject
    )

    decoded_subject = (
        decode_access_token(token)
    )

    assert decoded_subject == subject


def test_expired_access_token_is_rejected():
    token = create_access_token(
        subject=(
            "employee@company.com"
        ),
        expires_delta=timedelta(
            seconds=-1
        ),
    )

    assert (
        decode_access_token(token)
        is None
    )


def test_invalid_access_token_is_rejected():
    assert (
        decode_access_token(
            "not-a-valid-jwt"
        )
        is None
    )