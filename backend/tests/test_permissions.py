from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.permissions import (
    require_authenticated_user,
    require_roles,
)
from app.db.models import UserRole


def build_user(
    role: str,
):
    return SimpleNamespace(
        id=1,
        email=(
            "test.user@company.com"
        ),
        role=role,
        is_active=True,
    )


def test_authenticated_user_is_returned():
    user = build_user(
        UserRole.EMPLOYEE.value
    )

    result = (
        require_authenticated_user(
            current_user=user
        )
    )

    assert result is user


def test_hr_admin_can_access_hr_route():
    user = build_user(
        UserRole.HR_ADMIN.value
    )

    role_checker = require_roles(
        UserRole.HR_ADMIN.value
    )

    result = role_checker(
        current_user=user
    )

    assert result is user


def test_employee_cannot_access_hr_route():
    user = build_user(
        UserRole.EMPLOYEE.value
    )

    role_checker = require_roles(
        UserRole.HR_ADMIN.value
    )

    with pytest.raises(
        HTTPException
    ) as error:
        role_checker(
            current_user=user
        )

    assert (
        error.value.status_code
        == 403
    )


def test_finance_admin_cannot_access_hr_route():
    user = build_user(
        UserRole.FINANCE_ADMIN.value
    )

    role_checker = require_roles(
        UserRole.HR_ADMIN.value
    )

    with pytest.raises(
        HTTPException
    ) as error:
        role_checker(
            current_user=user
        )

    assert (
        error.value.status_code
        == 403
    )


def test_super_admin_can_access_hr_route():
    user = build_user(
        UserRole.SUPER_ADMIN.value
    )

    role_checker = require_roles(
        UserRole.HR_ADMIN.value
    )

    result = role_checker(
        current_user=user
    )

    assert result is user


def test_one_of_multiple_roles_is_accepted():
    user = build_user(
        UserRole.IT_ADMIN.value
    )

    role_checker = require_roles(
        UserRole.FINANCE_ADMIN.value,
        UserRole.IT_ADMIN.value,
    )

    result = role_checker(
        current_user=user
    )

    assert result is user