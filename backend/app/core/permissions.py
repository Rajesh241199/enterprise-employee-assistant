from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.api.auth import get_current_user
from app.db.models import User, UserRole


def require_authenticated_user(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user


def require_roles(*allowed_roles: str) -> Callable:
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role == UserRole.SUPER_ADMIN.value:
            return current_user

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )

        return current_user

    return role_checker