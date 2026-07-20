from sqlalchemy.orm import Session

from app.db.models import (
    EmployeeOnboardingProfile,
    User,
)
from app.schemas.onboarding import (
    OnboardingContact,
    OnboardingEmployeeDetails,
    OnboardingManagerDetails,
    OnboardingPOCDetails,
    OnboardingProfileResponse,
    OnboardingProjectDetails,
)
from app.services.poc_lookup import (
    get_relevant_poc_mapping,
    get_user_department_name,
)


def get_onboarding_profile_record(
    db: Session,
    current_user: User,
) -> EmployeeOnboardingProfile | None:
    return (
        db.query(EmployeeOnboardingProfile)
        .filter(
            EmployeeOnboardingProfile.user_id
            == current_user.id
        )
        .first()
    )


def build_mapping_contact(
    mapping: dict | None,
    name_field: str,
    email_field: str,
) -> OnboardingContact:
    if not mapping:
        return OnboardingContact()

    return OnboardingContact(
        name=mapping.get(name_field),
        email=mapping.get(email_field),
    )


def build_employee_buddy_contact(
    profile: EmployeeOnboardingProfile | None,
) -> OnboardingContact:
    if not profile:
        return OnboardingContact()

    return OnboardingContact(
        name=profile.buddy_name,
        email=profile.buddy_email,
    )


def has_value(value) -> bool:
    if value is None:
        return False

    return bool(str(value).strip())


def build_onboarding_profile(
    db: Session,
    current_user: User,
) -> OnboardingProfileResponse:
    profile = get_onboarding_profile_record(
        db=db,
        current_user=current_user,
    )

    poc_mapping = get_relevant_poc_mapping(
        db=db,
        current_user=current_user,
    )

    department_name = get_user_department_name(
        current_user
    )

    employee_details = OnboardingEmployeeDetails(
        employee_id=current_user.employee_id,
        full_name=current_user.full_name,
        email=current_user.email,
        designation=current_user.designation,
        location=current_user.location,
        department=department_name,
        business_unit=(
            profile.business_unit
            if profile
            else None
        ),
    )

    manager_details = OnboardingManagerDetails(
        name=(
            profile.manager_name
            if profile
            else None
        ),
        email=(
            profile.manager_email
            if profile
            else None
        ),
    )

    project_details = OnboardingProjectDetails(
        name=(
            profile.project_name
            if profile
            else None
        ),
        role=(
            profile.project_role
            if profile
            else None
        ),
        start_date=(
            profile.project_start_date
            if profile
            else None
        ),
    )

    poc_details = OnboardingPOCDetails(
        hr_poc=build_mapping_contact(
            poc_mapping,
            "hr_poc_name",
            "hr_poc_email",
        ),
        it_poc=build_mapping_contact(
            poc_mapping,
            "it_poc_name",
            "it_poc_email",
        ),
        buddy=build_employee_buddy_contact(
            profile
        ),
    )

    required_values = [
        employee_details.department,
        employee_details.business_unit,
        manager_details.name,
        manager_details.email,
        project_details.name,
        project_details.role,
        project_details.start_date,
        poc_details.hr_poc.name,
        poc_details.hr_poc.email,
        poc_details.it_poc.name,
        poc_details.it_poc.email,
        poc_details.buddy.name,
        poc_details.buddy.email,
    ]

    profile_complete = all(
        has_value(value)
        for value in required_values
    )

    return OnboardingProfileResponse(
        employee=employee_details,
        manager=manager_details,
        project=project_details,
        poc=poc_details,
        onboarding_status=(
            profile.onboarding_status
            if profile
            else "not_assigned"
        ),
        profile_complete=profile_complete,
    )


def value_or_pending(value) -> str:
    if not has_value(value):
        return "Not assigned yet"

    return str(value).strip()


def answer_onboarding_question(
    db: Session,
    query: str,
    current_user: User,
) -> tuple[str, int]:
    profile = build_onboarding_profile(
        db=db,
        current_user=current_user,
    )

    normalized_query = query.lower()

    if (
        "manager" in normalized_query
        or "reporting to" in normalized_query
        or "report to" in normalized_query
    ):
        manager_name = value_or_pending(
            profile.manager.name
        )

        manager_email = value_or_pending(
            profile.manager.email
        )

        answer = (
            "Your reporting manager is:\n"
            f"- Name: {manager_name}\n"
            f"- Email: {manager_email}"
        )

        return answer, 1

    if (
        "business unit" in normalized_query
        or "business vertical" in normalized_query
    ):
        business_unit = value_or_pending(
            profile.employee.business_unit
        )

        return (
            f"Your business unit is {business_unit}.",
            1,
        )

    if "department" in normalized_query:
        department = value_or_pending(
            profile.employee.department
        )

        return (
            f"Your department is {department}.",
            1,
        )

    if (
        "project" in normalized_query
        or "assignment" in normalized_query
    ):
        project_name = value_or_pending(
            profile.project.name
        )

        project_role = value_or_pending(
            profile.project.role
        )

        project_start_date = value_or_pending(
            profile.project.start_date
        )

        answer = (
            "Your current project assignment is:\n"
            f"- Project: {project_name}\n"
            f"- Project role: {project_role}\n"
            f"- Start date: {project_start_date}"
        )

        return answer, 1

    employee_designation = value_or_pending(
        profile.employee.designation
    )

    employee_location = value_or_pending(
        profile.employee.location
    )

    employee_department = value_or_pending(
        profile.employee.department
    )

    employee_business_unit = value_or_pending(
        profile.employee.business_unit
    )

    manager_name = value_or_pending(
        profile.manager.name
    )

    manager_email = value_or_pending(
        profile.manager.email
    )

    project_name = value_or_pending(
        profile.project.name
    )

    project_role = value_or_pending(
        profile.project.role
    )

    project_start_date = value_or_pending(
        profile.project.start_date
    )

    hr_poc_name = value_or_pending(
        profile.poc.hr_poc.name
    )

    hr_poc_email = value_or_pending(
        profile.poc.hr_poc.email
    )

    it_poc_name = value_or_pending(
        profile.poc.it_poc.name
    )

    it_poc_email = value_or_pending(
        profile.poc.it_poc.email
    )

    buddy_name = value_or_pending(
        profile.poc.buddy.name
    )

    buddy_email = value_or_pending(
        profile.poc.buddy.email
    )

    answer = (
        "Here are your onboarding details:\n"
        f"- Employee ID: {profile.employee.employee_id}\n"
        f"- Name: {profile.employee.full_name}\n"
        f"- Designation: {employee_designation}\n"
        f"- Location: {employee_location}\n"
        f"- Department: {employee_department}\n"
        f"- Business unit: {employee_business_unit}\n"
        f"- Reporting manager: "
        f"{manager_name} ({manager_email})\n"
        f"- Assigned project: {project_name}\n"
        f"- Project role: {project_role}\n"
        f"- Project start date: "
        f"{project_start_date}\n"
        f"- HR POC: "
        f"{hr_poc_name} ({hr_poc_email})\n"
        f"- IT POC: "
        f"{it_poc_name} ({it_poc_email})\n"
        f"- Onboarding buddy: "
        f"{buddy_name} ({buddy_email})"
    )

    return answer, 1