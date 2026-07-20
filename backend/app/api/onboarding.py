from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
)
from sqlalchemy.orm import Session

from app.core.permissions import (
    require_authenticated_user,
)
from app.db.models import User
from app.db.session import get_db
from app.schemas.onboarding import (
    OnboardingProfileResponse,
)
from app.services.audit_logger import audit_event
from app.services.onboarding_service import (
    build_onboarding_profile,
)


router = APIRouter()


def get_user_role_value(
    current_user: User,
) -> str:
    role = getattr(
        current_user,
        "role",
        "",
    )

    if hasattr(role, "value"):
        return str(role.value)

    return str(role)


def get_client_ip(
    request: Request,
) -> str:
    forwarded_for = request.headers.get(
        "X-Forwarded-For"
    )

    if forwarded_for:
        return (
            forwarded_for
            .split(",")[0]
            .strip()
        )

    if request.client:
        return request.client.host

    return "unknown"


@router.get(
    "/onboarding/me",
    response_model=OnboardingProfileResponse,
)
def get_my_onboarding_profile(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_authenticated_user
    ),
):
    response.headers[
        "Cache-Control"
    ] = "private, no-store, max-age=0"

    response.headers[
        "Pragma"
    ] = "no-cache"

    profile = build_onboarding_profile(
        db=db,
        current_user=current_user,
    )

    audit_event(
        event_type=(
            "onboarding.profile_viewed"
        ),
        outcome="success",
        request_id=getattr(
            request.state,
            "request_id",
            None,
        ),
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        actor_role=get_user_role_value(
            current_user
        ),
        client_ip=get_client_ip(request),
        user_agent=request.headers.get(
            "user-agent",
            "unknown",
        ),
        resource_type=(
            "employee_onboarding_profile"
        ),
        resource_id=str(current_user.id),
        metadata={
            "profile_complete": (
                profile.profile_complete
            ),
            "onboarding_status": (
                profile.onboarding_status
            ),
        },
    )

    return profile