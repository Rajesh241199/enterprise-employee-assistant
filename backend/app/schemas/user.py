import re

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


def validate_secure_password(
    value: str,
) -> str:
    if len(value) < 12:
        raise ValueError(
            "Password must contain at least "
            "12 characters."
        )

    if len(value.encode("utf-8")) > 72:
        raise ValueError(
            "Password must not exceed "
            "72 bytes."
        )

    if not re.search(r"[A-Z]", value):
        raise ValueError(
            "Password must contain at least "
            "one uppercase letter."
        )

    if not re.search(r"[a-z]", value):
        raise ValueError(
            "Password must contain at least "
            "one lowercase letter."
        )

    if not re.search(r"\d", value):
        raise ValueError(
            "Password must contain at least "
            "one number."
        )

    if not re.search(
        r"[^A-Za-z0-9]",
        value,
    ):
        raise ValueError(
            "Password must contain at least "
            "one special character."
        )

    return value


class LoginRequest(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=1,
        max_length=128,
    )


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
    must_change_password: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(
        min_length=1,
        max_length=128,
    )

    new_password: str = Field(
        min_length=12,
        max_length=128,
    )

    confirm_password: str = Field(
        min_length=12,
        max_length=128,
    )

    @field_validator(
        "new_password",
        "confirm_password",
    )
    @classmethod
    def validate_password_strength(
        cls,
        value: str,
    ) -> str:
        return validate_secure_password(
            value
        )

    @model_validator(mode="after")
    def validate_password_confirmation(
        self,
    ):
        if (
            self.new_password
            != self.confirm_password
        ):
            raise ValueError(
                "New password and confirmation "
                "password do not match."
            )

        if (
            self.current_password
            == self.new_password
        ):
            raise ValueError(
                "New password must be different "
                "from the current password."
            )

        return self


class ChangePasswordResponse(BaseModel):
    message: str
    must_change_password: bool