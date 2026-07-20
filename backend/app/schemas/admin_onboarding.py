from datetime import date

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.schemas.onboarding import (
    OnboardingEmployeeDetails,
    OnboardingManagerDetails,
    OnboardingPOCDetails,
    OnboardingProjectDetails,
)


class AdminPOCInput(BaseModel):
    hr_poc_name: str | None = Field(
        default=None,
        max_length=150,
    )

    hr_poc_email: EmailStr | None = None

    it_poc_name: str | None = Field(
        default=None,
        max_length=150,
    )

    it_poc_email: EmailStr | None = None

    buddy_name: str | None = Field(
        default=None,
        max_length=150,
    )

    buddy_email: EmailStr | None = None

    @field_validator(
        "hr_poc_name",
        "it_poc_name",
        "buddy_name",
        mode="before",
    )
    @classmethod
    def normalize_optional_names(
        cls,
        value,
    ):
        if value is None:
            return None

        normalized = str(value).strip()

        return normalized or None


class AdminEmployeeOnboardingCreate(
    AdminPOCInput
):
    employee_id: str = Field(
        min_length=2,
        max_length=50,
    )

    full_name: str = Field(
        min_length=2,
        max_length=150,
    )

    email: EmailStr

    temporary_password: str = Field(
        min_length=12,
        max_length=128,
    )

    designation: str | None = Field(
        default=None,
        max_length=150,
    )

    location: str = Field(
        min_length=2,
        max_length=100,
    )

    department: str = Field(
        min_length=2,
        max_length=100,
    )

    business_unit: str | None = Field(
        default=None,
        max_length=150,
    )

    manager_name: str | None = Field(
        default=None,
        max_length=150,
    )

    manager_email: EmailStr | None = None

    project_name: str | None = Field(
        default=None,
        max_length=255,
    )

    project_role: str | None = Field(
        default=None,
        max_length=150,
    )

    project_start_date: date | None = None

    onboarding_status: str = Field(
        default="assigned",
        min_length=2,
        max_length=50,
    )

    is_active: bool = True

    @field_validator(
        "employee_id",
        "full_name",
        "location",
        "department",
        "onboarding_status",
        mode="before",
    )
    @classmethod
    def normalize_required_text(
        cls,
        value,
    ):
        return str(value).strip()

    @field_validator(
        "designation",
        "business_unit",
        "manager_name",
        "project_name",
        "project_role",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value,
    ):
        if value is None:
            return None

        normalized = str(value).strip()

        return normalized or None

    @field_validator(
        "temporary_password"
    )
    @classmethod
    def validate_bcrypt_password_length(
        cls,
        value: str,
    ) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError(
                "Temporary password must not "
                "exceed 72 bytes."
            )

        return value

    @model_validator(mode="after")
    def validate_related_fields(self):
        if (
            self.manager_name
            and not self.manager_email
        ):
            raise ValueError(
                "Manager email is required when "
                "manager name is provided."
            )

        if (
            self.manager_email
            and not self.manager_name
        ):
            raise ValueError(
                "Manager name is required when "
                "manager email is provided."
            )

        if (
            self.project_start_date
            and not self.project_name
        ):
            raise ValueError(
                "Project name is required when "
                "project start date is provided."
            )

        return self


class AdminEmployeeOnboardingUpdate(
    AdminPOCInput
):
    employee_id: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )

    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )

    email: EmailStr | None = None

    new_temporary_password: str | None = Field(
        default=None,
        min_length=12,
        max_length=128,
    )

    designation: str | None = Field(
        default=None,
        max_length=150,
    )

    location: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    department: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    business_unit: str | None = Field(
        default=None,
        max_length=150,
    )

    manager_name: str | None = Field(
        default=None,
        max_length=150,
    )

    manager_email: EmailStr | None = None

    project_name: str | None = Field(
        default=None,
        max_length=255,
    )

    project_role: str | None = Field(
        default=None,
        max_length=150,
    )

    project_start_date: date | None = None

    onboarding_status: str | None = Field(
        default=None,
        min_length=2,
        max_length=50,
    )

    is_active: bool | None = None

    @field_validator(
        "employee_id",
        "full_name",
        "location",
        "department",
        "designation",
        "business_unit",
        "manager_name",
        "project_name",
        "project_role",
        "onboarding_status",
        mode="before",
    )
    @classmethod
    def normalize_update_text(
        cls,
        value,
    ):
        if value is None:
            return None

        normalized = str(value).strip()

        return normalized or None

    @field_validator(
        "new_temporary_password"
    )
    @classmethod
    def validate_new_password(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        if len(value.encode("utf-8")) > 72:
            raise ValueError(
                "Temporary password must not "
                "exceed 72 bytes."
            )

        return value


class AdminEmployeeOnboardingResponse(
    BaseModel
):
    user_id: int
    is_active: bool
    role: str

    employee: OnboardingEmployeeDetails
    manager: OnboardingManagerDetails
    project: OnboardingProjectDetails
    poc: OnboardingPOCDetails

    onboarding_status: str
    profile_complete: bool


class AdminEmployeeOnboardingListResponse(
    BaseModel
):
    items: list[
        AdminEmployeeOnboardingResponse
    ]

    total: int
    offset: int
    limit: int