from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserProfileResponse(BaseModel):
    id: int
    employee_id: str
    full_name: str
    email: EmailStr
    role: str
    location: str | None = None
    designation: str | None = None
    department: str | None = None