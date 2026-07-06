from fastapi import APIRouter, Depends

from app.core.permissions import require_roles
from app.db.models import User, UserRole


router = APIRouter()


@router.get("/admin/hr-only")
def hr_admin_only(
    current_user: User = Depends(
        require_roles(UserRole.HR_ADMIN.value)
    ),
):
    return {
        "message": "You have access to HR admin resources.",
        "user": current_user.email,
        "role": current_user.role,
    }


@router.get("/admin/finance-only")
def finance_admin_only(
    current_user: User = Depends(
        require_roles(UserRole.FINANCE_ADMIN.value)
    ),
):
    return {
        "message": "You have access to Finance admin resources.",
        "user": current_user.email,
        "role": current_user.role,
    }


@router.get("/admin/super-admin-only")
def super_admin_only(
    current_user: User = Depends(
        require_roles(UserRole.SUPER_ADMIN.value)
    ),
):
    return {
        "message": "You have access to Super Admin resources.",
        "user": current_user.email,
        "role": current_user.role,
    }