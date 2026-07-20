from datetime import date

from pydantic import BaseModel, EmailStr


class OnboardingContact(BaseModel):
    name: str | None = None
    email: EmailStr | None = None


class OnboardingEmployeeDetails(BaseModel):
    employee_id: str
    full_name: str
    email: EmailStr

    designation: str | None = None
    location: str | None = None
    department: str | None = None
    business_unit: str | None = None


class OnboardingManagerDetails(BaseModel):
    name: str | None = None
    email: EmailStr | None = None


class OnboardingProjectDetails(BaseModel):
    name: str | None = None
    role: str | None = None
    start_date: date | None = None


class OnboardingPOCDetails(BaseModel):
    hr_poc: OnboardingContact
    it_poc: OnboardingContact
    buddy: OnboardingContact


class OnboardingProfileResponse(BaseModel):
    employee: OnboardingEmployeeDetails
    manager: OnboardingManagerDetails
    project: OnboardingProjectDetails
    poc: OnboardingPOCDetails

    onboarding_status: str
    profile_complete: bool