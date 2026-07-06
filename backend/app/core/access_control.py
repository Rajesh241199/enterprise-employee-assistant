from fastapi import HTTPException, status

from app.db.models import User


ROLE_ACCESS_LEVEL_MAP = {
    "employee": ["all_employees"],
    "hr_admin": ["all_employees", "hr_only"],
    "finance_admin": ["all_employees", "finance_only"],
    "it_admin": ["all_employees", "it_only"],
    "super_admin": [
        "all_employees",
        "hr_only",
        "finance_only",
        "it_only",
        "leadership_only",
        "admin_only",
        "confidential",
    ],
}


def normalize_role(role: object) -> str:
    """
    Supports role values like:
    - employee
    - hr_admin
    - HR Admin
    - Role.HR_ADMIN
    """

    if role is None:
        return "employee"

    raw_role = getattr(role, "value", role)
    normalized = str(raw_role).strip().lower()
    normalized = normalized.replace(" ", "_")
    normalized = normalized.replace("-", "_")

    return normalized


def get_allowed_access_levels_for_user(user: User) -> list[str]:
    role = normalize_role(getattr(user, "role", None))

    return ROLE_ACCESS_LEVEL_MAP.get(role, ["all_employees"])


def resolve_rag_access_levels(
    user: User,
    requested_access_level: str | None = None,
) -> list[str]:
    """
    Server-side access control for RAG retrieval.

    Rules:
    - Employee can only access all_employees.
    - HR Admin can access all_employees + hr_only.
    - Finance Admin can access all_employees + finance_only.
    - IT Admin can access all_employees + it_only.
    - Super Admin can access all configured document access levels.

    If the user manually requests an unauthorized access_level,
    block it with 403.
    """

    allowed_access_levels = get_allowed_access_levels_for_user(user)

    if requested_access_level is None:
        return allowed_access_levels

    requested = requested_access_level.strip()

    if requested not in allowed_access_levels:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "You do not have permission to access documents with "
                f"access_level='{requested}'."
            ),
        )

    return [requested]