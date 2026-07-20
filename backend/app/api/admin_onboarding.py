from fastapi import (
    APIRouter,
    Depends,
    Query,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.core.permissions import require_roles
from app.db.models import User, UserRole
from app.db.session import get_db
from app.schemas.admin_onboarding import (
    AdminEmployeeOnboardingCreate,
    AdminEmployeeOnboardingListResponse,
    AdminEmployeeOnboardingResponse,
    AdminEmployeeOnboardingUpdate,
)
from app.services.admin_onboarding_service import (
    build_admin_employee_response,
    create_employee_onboarding,
    get_employee_or_404,
    list_employee_onboarding_records,
    update_employee_onboarding,
)
from app.services.audit_logger import audit_event


router = APIRouter()


def get_actor_role(
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


def write_admin_audit_event(
    request: Request,
    current_user: User,
    event_type: str,
    outcome: str,
    target_user_id: int | None = None,
    metadata: dict | None = None,
) -> None:
    audit_event(
        event_type=event_type,
        outcome=outcome,
        request_id=getattr(
            request.state,
            "request_id",
            None,
        ),
        actor_user_id=current_user.id,
        actor_email=current_user.email,
        actor_role=get_actor_role(
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
        resource_id=target_user_id,
        metadata=metadata or {},
    )


@router.post(
    "/admin/onboarding/employees",
    response_model=(
        AdminEmployeeOnboardingResponse
    ),
    status_code=status.HTTP_201_CREATED,
)
def create_employee(
    payload: AdminEmployeeOnboardingCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.HR_ADMIN.value
        )
    ),
):
    response.headers[
        "Cache-Control"
    ] = "private, no-store, max-age=0"

    created_employee = (
        create_employee_onboarding(
            db=db,
            payload=payload,
        )
    )

    write_admin_audit_event(
        request=request,
        current_user=current_user,
        event_type=(
            "admin.onboarding.employee_created"
        ),
        outcome="success",
        target_user_id=(
            created_employee.user_id
        ),
        metadata={
            "employee_id": (
                created_employee
                .employee
                .employee_id
            ),
            "department": (
                created_employee
                .employee
                .department
            ),
            "business_unit": (
                created_employee
                .employee
                .business_unit
            ),
            "profile_complete": (
                created_employee
                .profile_complete
            ),
        },
    )

    return created_employee


@router.get(
    "/admin/onboarding/employees",
    response_model=(
        AdminEmployeeOnboardingListResponse
    ),
)
def list_employees(
    request: Request,
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
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.HR_ADMIN.value
        )
    ),
):
    response.headers[
        "Cache-Control"
    ] = "private, no-store, max-age=0"

    result = (
        list_employee_onboarding_records(
            db=db,
            offset=offset,
            limit=limit,
        )
    )

    write_admin_audit_event(
        request=request,
        current_user=current_user,
        event_type=(
            "admin.onboarding.employee_list_viewed"
        ),
        outcome="success",
        metadata={
            "offset": offset,
            "limit": limit,
            "returned_count": (
                len(result.items)
            ),
            "total": result.total,
        },
    )

    return result


@router.get(
    "/admin/onboarding/employees/{user_id}",
    response_model=(
        AdminEmployeeOnboardingResponse
    ),
)
def get_employee(
    user_id: int,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.HR_ADMIN.value
        )
    ),
):
    response.headers[
        "Cache-Control"
    ] = "private, no-store, max-age=0"

    employee = get_employee_or_404(
        db=db,
        user_id=user_id,
    )

    result = build_admin_employee_response(
        db=db,
        employee=employee,
    )

    write_admin_audit_event(
        request=request,
        current_user=current_user,
        event_type=(
            "admin.onboarding.employee_viewed"
        ),
        outcome="success",
        target_user_id=user_id,
        metadata={
            "employee_id": (
                result.employee.employee_id
            ),
        },
    )

    return result


@router.put(
    "/admin/onboarding/employees/{user_id}",
    response_model=(
        AdminEmployeeOnboardingResponse
    ),
)
def update_employee(
    user_id: int,
    payload: AdminEmployeeOnboardingUpdate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.HR_ADMIN.value
        )
    ),
):
    response.headers[
        "Cache-Control"
    ] = "private, no-store, max-age=0"

    updated_employee = (
        update_employee_onboarding(
            db=db,
            user_id=user_id,
            payload=payload,
        )
    )

    write_admin_audit_event(
        request=request,
        current_user=current_user,
        event_type=(
            "admin.onboarding.employee_updated"
        ),
        outcome="success",
        target_user_id=user_id,
        metadata={
            "employee_id": (
                updated_employee
                .employee
                .employee_id
            ),
            "is_active": (
                updated_employee.is_active
            ),
            "onboarding_status": (
                updated_employee
                .onboarding_status
            ),
            "profile_complete": (
                updated_employee
                .profile_complete
            ),
            "password_changed": (
                payload
                .new_temporary_password
                is not None
            ),
        },
    )

    return updated_employee