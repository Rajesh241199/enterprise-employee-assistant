from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import (
    EmployeeOnboardingProfile,
    EmployeePOCMapping,
    User,
)


def get_user_department_name(
    current_user: User,
) -> str | None:
    department = getattr(
        current_user,
        "department",
        None,
    )

    if department is None:
        return None

    if hasattr(department, "name"):
        return str(department.name)

    department_text = str(
        department
    ).strip()

    return department_text or None


def detect_requested_poc_type(
    query: str,
) -> str:
    normalized_query = query.lower()

    hr_keywords = [
        "hr poc",
        "hr contact",
        "human resource",
        "human resources",
    ]

    it_keywords = [
        "it poc",
        "it contact",
        "technical contact",
        "technical support",
        "system support",
    ]

    buddy_keywords = [
        "buddy",
        "mentor",
        "onboarding partner",
    ]

    if any(
        keyword in normalized_query
        for keyword in buddy_keywords
    ):
        return "buddy"

    if any(
        keyword in normalized_query
        for keyword in hr_keywords
    ):
        return "hr"

    if any(
        keyword in normalized_query
        for keyword in it_keywords
    ):
        return "it"

    return "all"


def detect_requested_department(
    query: str,
) -> str | None:
    normalized_query = query.lower()

    department_keywords = {
        "data science": "Data Science",
        "finance": "Finance",
        "human resources": (
            "Human Resources"
        ),
        "hr department": (
            "Human Resources"
        ),
        "information technology": "IT",
        "it department": "IT",
    }

    for keyword, department in (
        department_keywords.items()
    ):
        if keyword in normalized_query:
            return department

    return None


def mapping_to_dict(
    mapping: EmployeePOCMapping | None,
) -> dict | None:
    if not mapping:
        return None

    return {
        "id": mapping.id,
        "department": mapping.department,
        "location": mapping.location,
        "hr_poc_name": mapping.hr_poc_name,
        "hr_poc_email": mapping.hr_poc_email,
        "it_poc_name": mapping.it_poc_name,
        "it_poc_email": mapping.it_poc_email,
    }


def get_relevant_poc_mapping(
    db: Session,
    current_user: User,
    requested_department: str | None = None,
) -> dict | None:
    user_department = get_user_department_name(
        current_user
    )

    user_location = getattr(
        current_user,
        "location",
        None,
    )

    target_department = (
        requested_department
        or user_department
    )

    if target_department and user_location:
        mapping = (
            db.query(EmployeePOCMapping)
            .filter(
                func.lower(
                    EmployeePOCMapping.department
                )
                == target_department.lower(),
                func.lower(
                    func.coalesce(
                        EmployeePOCMapping.location,
                        "",
                    )
                )
                == user_location.lower(),
            )
            .order_by(
                EmployeePOCMapping.id.asc()
            )
            .first()
        )

        if mapping:
            return mapping_to_dict(mapping)

    if target_department:
        mapping = (
            db.query(EmployeePOCMapping)
            .filter(
                func.lower(
                    EmployeePOCMapping.department
                )
                == target_department.lower()
            )
            .order_by(
                EmployeePOCMapping.id.asc()
            )
            .first()
        )

        if mapping:
            return mapping_to_dict(mapping)

    if user_location:
        mapping = (
            db.query(EmployeePOCMapping)
            .filter(
                func.lower(
                    func.coalesce(
                        EmployeePOCMapping.location,
                        "",
                    )
                )
                == user_location.lower()
            )
            .order_by(
                EmployeePOCMapping.id.asc()
            )
            .first()
        )

        if mapping:
            return mapping_to_dict(mapping)

    return None


def get_employee_buddy(
    db: Session,
    current_user: User,
) -> tuple[str | None, str | None]:
    profile = (
        db.query(EmployeeOnboardingProfile)
        .filter(
            EmployeeOnboardingProfile.user_id
            == current_user.id
        )
        .first()
    )

    if not profile:
        return None, None

    return (
        profile.buddy_name,
        profile.buddy_email,
    )


def display_contact(
    name: str | None,
    email: str | None,
) -> str:
    display_name = (
        name or "Not assigned"
    )

    display_email = (
        email or "No email"
    )

    return (
        f"{display_name} "
        f"({display_email})"
    )


def answer_poc_question(
    db: Session,
    query: str,
    current_user: User,
) -> tuple[str, int]:
    poc_type = detect_requested_poc_type(
        query
    )

    requested_department = (
        detect_requested_department(query)
    )

    mapping = get_relevant_poc_mapping(
        db=db,
        current_user=current_user,
        requested_department=(
            requested_department
        ),
    )

    buddy_name, buddy_email = (
        get_employee_buddy(
            db=db,
            current_user=current_user,
        )
    )

    department_name = (
        requested_department
        or get_user_department_name(
            current_user
        )
        or "your department"
    )

    location_name = (
        getattr(
            current_user,
            "location",
            None,
        )
        or "your location"
    )

    if mapping:
        department_name = (
            mapping.get("department")
            or department_name
        )

        location_name = (
            mapping.get("location")
            or location_name
        )

    if poc_type == "buddy":
        if not buddy_name and not buddy_email:
            return (
                "Your onboarding buddy has "
                "not been assigned yet.",
                0,
            )

        answer = (
            "Your onboarding buddy is:\n"
            f"- Name: "
            f"{buddy_name or 'Not assigned'}\n"
            f"- Email: "
            f"{buddy_email or 'Not assigned'}"
        )

        return answer, 1

    if poc_type == "hr":
        if not mapping:
            return (
                "I could not find an HR POC "
                "mapping for your department "
                "and location.",
                0,
            )

        answer = (
            f"Your HR POC for "
            f"{department_name} "
            f"({location_name}) is:\n"
            f"- Name: "
            f"{mapping.get('hr_poc_name') or 'Not assigned'}\n"
            f"- Email: "
            f"{mapping.get('hr_poc_email') or 'Not assigned'}"
        )

        return answer, 1

    if poc_type == "it":
        if not mapping:
            return (
                "I could not find an IT POC "
                "mapping for your department "
                "and location.",
                0,
            )

        answer = (
            f"Your IT POC for "
            f"{department_name} "
            f"({location_name}) is:\n"
            f"- Name: "
            f"{mapping.get('it_poc_name') or 'Not assigned'}\n"
            f"- Email: "
            f"{mapping.get('it_poc_email') or 'Not assigned'}"
        )

        return answer, 1

    hr_name = (
        mapping.get("hr_poc_name")
        if mapping
        else None
    )

    hr_email = (
        mapping.get("hr_poc_email")
        if mapping
        else None
    )

    it_name = (
        mapping.get("it_poc_name")
        if mapping
        else None
    )

    it_email = (
        mapping.get("it_poc_email")
        if mapping
        else None
    )

    answer = (
        "Here are your onboarding contacts "
        f"for {department_name} "
        f"({location_name}):\n"
        f"- HR POC: "
        f"{display_contact(hr_name, hr_email)}\n"
        f"- IT POC: "
        f"{display_contact(it_name, it_email)}\n"
        f"- Onboarding buddy: "
        f"{display_contact(buddy_name, buddy_email)}"
    )

    available_contacts = sum(
        [
            bool(hr_name or hr_email),
            bool(it_name or it_email),
            bool(
                buddy_name
                or buddy_email
            ),
        ]
    )

    return answer, available_contacts