from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
)
from sqlalchemy.orm import Session

from app.core.permissions import (
    require_roles,
)
from app.db.models import (
    User,
    UserRole,
)
from app.db.session import get_db
from app.schemas.audit import (
    AuditLogListResponse,
    AuditLogSummaryResponse,
)
from app.services.audit_log_service import (
    get_audit_log_summary,
    list_audit_logs,
)


router = APIRouter()


def set_private_headers(
    response: Response,
) -> None:
    response.headers[
        "Cache-Control"
    ] = (
        "private, no-store, "
        "max-age=0"
    )

    response.headers[
        "Pragma"
    ] = "no-cache"


@router.get(
    "/admin/audit-logs",
    response_model=(
        AuditLogListResponse
    ),
)
def get_audit_logs(
    response: Response,

    offset: int = Query(
        default=0,
        ge=0,
    ),

    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),

    event_type: str | None = Query(
        default=None,
        max_length=150,
    ),

    outcome: str | None = Query(
        default=None,
        max_length=50,
    ),

    actor_email: str | None = Query(
        default=None,
        max_length=255,
    ),

    actor_role: str | None = Query(
        default=None,
        max_length=50,
    ),

    resource_type:
        str | None = Query(
            default=None,
            max_length=100,
        ),

    start_time:
        datetime | None = Query(
            default=None,
        ),

    end_time:
        datetime | None = Query(
            default=None,
        ),

    db: Session = Depends(get_db),

    current_user:
        User = Depends(
            require_roles(
                UserRole.HR_ADMIN.value
            )
        ),
):
    del current_user

    set_private_headers(
        response
    )

    return list_audit_logs(
        db=db,
        offset=offset,
        limit=limit,
        event_type=event_type,
        outcome=outcome,
        actor_email=actor_email,
        actor_role=actor_role,
        resource_type=resource_type,
        start_time=start_time,
        end_time=end_time,
    )


@router.get(
    "/admin/audit-logs/summary",
    response_model=(
        AuditLogSummaryResponse
    ),
)
def get_audit_summary(
    response: Response,

    db: Session = Depends(get_db),

    current_user:
        User = Depends(
            require_roles(
                UserRole.HR_ADMIN.value
            )
        ),
):
    del current_user

    set_private_headers(
        response
    )

    return get_audit_log_summary(
        db=db
    )