from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_access_token, verify_password
from app.db.models import User
from app.db.session import get_db
from app.schemas.user import LoginRequest, TokenResponse, UserProfileResponse


router = APIRouter()

bearer_scheme = HTTPBearer()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


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
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(subject=user.email)

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
