from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_access_token, verify_password
from app.db.models import User
from app.db.session import get_db
from app.schemas.user import LoginRequest, TokenResponse, UserProfileResponse
from app.services.audit_logger import audit_event


router = APIRouter()

bearer_scheme = HTTPBearer()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "unknown"


def get_user_role_value(user: User) -> str | None:
    role = getattr(user, "role", None)

    if hasattr(role, "value"):
        return str(role.value)

    if role is not None:
        return str(role)

    return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials

    email = decode_access_token(token)

    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = get_user_by_email(db, email)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


@router.post("/auth/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    request_id = get_request_id(request)
    client_ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "unknown")

    user = get_user_by_email(db, payload.email)

    if not user:
        audit_event(
            event_type="auth.login_failed",
            outcome="failure",
            request_id=request_id,
            actor_email=payload.email,
            client_ip=client_ip,
            user_agent=user_agent,
            resource_type="auth",
            metadata={
                "reason": "user_not_found",
            },
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(payload.password, user.hashed_password):
        audit_event(
            event_type="auth.login_failed",
            outcome="failure",
            request_id=request_id,
            actor_user_id=user.id,
            actor_email=user.email,
            actor_role=get_user_role_value(user),
            client_ip=client_ip,
            user_agent=user_agent,
            resource_type="auth",
            metadata={
                "reason": "invalid_password",
            },
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(subject=user.email)

    audit_event(
        event_type="auth.login_success",
        outcome="success",
        request_id=request_id,
        actor_user_id=user.id,
        actor_email=user.email,
        actor_role=get_user_role_value(user),
        client_ip=client_ip,
        user_agent=user_agent,
        resource_type="auth",
        metadata={
            "employee_id": getattr(user, "employee_id", None),
            "full_name": getattr(user, "full_name", None),
        },
    )

    return TokenResponse(access_token=access_token)


@router.get("/auth/me", response_model=UserProfileResponse)
def get_me(current_user: User = Depends(get_current_user)):
    department_name = None

    if current_user.department:
        department_name = current_user.department.name

    return UserProfileResponse(
        id=current_user.id,
        employee_id=current_user.employee_id,
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role,
        location=current_user.location,
        designation=current_user.designation,
        department=department_name,
    )