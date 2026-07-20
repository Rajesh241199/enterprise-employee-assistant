from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.db.models import User
from app.db.session import get_db
from app.schemas.user import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    LoginRequest,
    TokenResponse,
    UserProfileResponse,
)
from app.services.audit_logger import (
    audit_event,
)
from app.services.password_security_service import (
    is_password_change_required,
    mark_password_changed,
)


router = APIRouter()

bearer_scheme = HTTPBearer()


PASSWORD_CHANGE_ALLOWED_PATHS = {
    "/api/auth/me",
    "/api/auth/change-password",
}


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    normalized_email = (
        email.strip().lower()
    )

    return (
        db.query(User)
        .filter(
            User.email
            == normalized_email
        )
        .first()
    )


def get_request_id(
    request: Request,
) -> str | None:
    return getattr(
        request.state,
        "request_id",
        None,
    )


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


def get_user_role_value(
    user: User,
) -> str | None:
    role = getattr(
        user,
        "role",
        None,
    )

    if hasattr(role, "value"):
        return str(role.value)

    if role is not None:
        return str(role)

    return None


def get_current_user(
    request: Request,
    credentials:
        HTTPAuthorizationCredentials
        = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    email = decode_access_token(
        token
    )

    if email is None:
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid or expired token"
            ),
        )

    user = get_user_by_email(
        db,
        email,
    )

    if (
        not user
        or not user.is_active
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "User not found or inactive"
            ),
        )

    password_change_required = (
        is_password_change_required(
            db=db,
            user_id=user.id,
        )
    )

    if (
        password_change_required
        and request.url.path
        not in PASSWORD_CHANGE_ALLOWED_PATHS
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_403_FORBIDDEN
            ),
            detail=(
                "Password change required "
                "before accessing this resource."
            ),
            headers={
                "X-Password-Change-Required":
                    "true",
            },
        )

    return user


@router.post(
    "/auth/login",
    response_model=TokenResponse,
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    request_id = get_request_id(
        request
    )

    client_ip = get_client_ip(
        request
    )

    user_agent = request.headers.get(
        "user-agent",
        "unknown",
    )

    normalized_email = (
        str(payload.email)
        .strip()
        .lower()
    )

    user = get_user_by_email(
        db,
        normalized_email,
    )

    if not user:
        audit_event(
            event_type=(
                "auth.login_failed"
            ),
            outcome="failure",
            request_id=request_id,
            actor_email=normalized_email,
            client_ip=client_ip,
            user_agent=user_agent,
            resource_type="auth",
            metadata={
                "reason":
                    "user_not_found",
            },
        )

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid email or password"
            ),
        )

    if not user.is_active:
        audit_event(
            event_type=(
                "auth.login_failed"
            ),
            outcome="failure",
            request_id=request_id,
            actor_user_id=user.id,
            actor_email=user.email,
            actor_role=(
                get_user_role_value(user)
            ),
            client_ip=client_ip,
            user_agent=user_agent,
            resource_type="auth",
            metadata={
                "reason":
                    "inactive_account",
            },
        )

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid email or password"
            ),
        )

    if not verify_password(
        payload.password,
        user.hashed_password,
    ):
        audit_event(
            event_type=(
                "auth.login_failed"
            ),
            outcome="failure",
            request_id=request_id,
            actor_user_id=user.id,
            actor_email=user.email,
            actor_role=(
                get_user_role_value(user)
            ),
            client_ip=client_ip,
            user_agent=user_agent,
            resource_type="auth",
            metadata={
                "reason":
                    "invalid_password",
            },
        )

        raise HTTPException(
            status_code=(
                status.HTTP_401_UNAUTHORIZED
            ),
            detail=(
                "Invalid email or password"
            ),
        )

    access_token = create_access_token(
        subject=user.email
    )

    password_change_required = (
        is_password_change_required(
            db=db,
            user_id=user.id,
        )
    )

    response.headers[
        "Cache-Control"
    ] = (
        "no-store, no-cache, "
        "must-revalidate, private"
    )

    response.headers[
        "Pragma"
    ] = "no-cache"

    audit_event(
        event_type=(
            "auth.login_success"
        ),
        outcome="success",
        request_id=request_id,
        actor_user_id=user.id,
        actor_email=user.email,
        actor_role=(
            get_user_role_value(user)
        ),
        client_ip=client_ip,
        user_agent=user_agent,
        resource_type="auth",
        metadata={
            "employee_id":
                getattr(
                    user,
                    "employee_id",
                    None,
                ),
            "full_name":
                getattr(
                    user,
                    "full_name",
                    None,
                ),
            "password_change_required":
                password_change_required,
        },
    )

    return TokenResponse(
        access_token=access_token
    )


@router.get(
    "/auth/me",
    response_model=UserProfileResponse,
)
def get_me(
    response: Response,
    current_user:
        User = Depends(
            get_current_user
        ),
    db: Session = Depends(get_db),
):
    department_name = None

    if current_user.department:
        department_name = (
            current_user.department.name
        )

    response.headers[
        "Cache-Control"
    ] = (
        "no-store, no-cache, "
        "must-revalidate, private"
    )

    response.headers[
        "Pragma"
    ] = "no-cache"

    return UserProfileResponse(
        id=current_user.id,
        employee_id=(
            current_user.employee_id
        ),
        full_name=(
            current_user.full_name
        ),
        email=current_user.email,
        role=current_user.role,
        location=current_user.location,
        designation=(
            current_user.designation
        ),
        department=department_name,
        must_change_password=(
            is_password_change_required(
                db=db,
                user_id=current_user.id,
            )
        ),
    )


@router.post(
    "/auth/change-password",
    response_model=(
        ChangePasswordResponse
    ),
)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    current_user:
        User = Depends(
            get_current_user
        ),
    db: Session = Depends(get_db),
):
    request_id = get_request_id(
        request
    )

    client_ip = get_client_ip(
        request
    )

    user_agent = request.headers.get(
        "user-agent",
        "unknown",
    )

    if not verify_password(
        payload.current_password,
        current_user.hashed_password,
    ):
        audit_event(
            event_type=(
                "auth.password_change_failed"
            ),
            outcome="failure",
            request_id=request_id,
            actor_user_id=(
                current_user.id
            ),
            actor_email=(
                current_user.email
            ),
            actor_role=(
                get_user_role_value(
                    current_user
                )
            ),
            client_ip=client_ip,
            user_agent=user_agent,
            resource_type="auth",
            resource_id=str(
                current_user.id
            ),
            metadata={
                "reason":
                    "invalid_current_password",
            },
        )

        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "Current password is incorrect."
            ),
        )

    if verify_password(
        payload.new_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=(
                "New password must be different "
                "from the current password."
            ),
        )

    try:
        current_user.hashed_password = (
            hash_password(
                payload.new_password
            )
        )

        db.flush()

        mark_password_changed(
            db=db,
            user_id=current_user.id,
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    response.headers[
        "Cache-Control"
    ] = (
        "no-store, no-cache, "
        "must-revalidate, private"
    )

    response.headers[
        "Pragma"
    ] = "no-cache"

    audit_event(
        event_type=(
            "auth.password_changed"
        ),
        outcome="success",
        request_id=request_id,
        actor_user_id=(
            current_user.id
        ),
        actor_email=(
            current_user.email
        ),
        actor_role=(
            get_user_role_value(
                current_user
            )
        ),
        client_ip=client_ip,
        user_agent=user_agent,
        resource_type="auth",
        resource_id=str(
            current_user.id
        ),
        metadata={
            "forced_change_completed":
                True,
        },
    )

    return ChangePasswordResponse(
        message=(
            "Password changed successfully."
        ),
        must_change_password=False,
    )