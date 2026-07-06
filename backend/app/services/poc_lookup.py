from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.models import User


def detect_requested_poc_type(query: str) -> str:
    normalized_query = query.lower()

    if "hr" in normalized_query or "human resource" in normalized_query:
        return "hr"

    if "it" in normalized_query or "technical" in normalized_query or "system" in normalized_query:
        return "it"

    if "buddy" in normalized_query or "mentor" in normalized_query:
        return "buddy"

    return "all"


def detect_requested_department(query: str) -> str | None:
    normalized_query = query.lower()

    department_keywords = {
        "data science": "Data Science",
        "finance": "Finance",
        "human resources": "Human Resources",
        "hr": "Human Resources",
        "it": "IT",
    }

    for keyword, department in department_keywords.items():
        if keyword in normalized_query:
            return department

    return None


def get_relevant_poc_mapping(
    db: Session,
    current_user: User,
    requested_department: str | None = None,
) -> dict | None:
    user_department = getattr(current_user, "department", None)
    user_location = getattr(current_user, "location", None)

    target_department = requested_department or user_department

    if target_department and user_location:
        query = text(
            """
            SELECT *
            FROM employee_poc_mapping
            WHERE LOWER(department) = LOWER(:department)
              AND LOWER(location) = LOWER(:location)
            ORDER BY id ASC
            LIMIT 1
            """
        )

        row = db.execute(
            query,
            {
                "department": target_department,
                "location": user_location,
            },
        ).mappings().first()

        if row:
            return dict(row)

    if target_department:
        query = text(
            """
            SELECT *
            FROM employee_poc_mapping
            WHERE LOWER(department) = LOWER(:department)
            ORDER BY id ASC
            LIMIT 1
            """
        )

        row = db.execute(
            query,
            {"department": target_department},
        ).mappings().first()

        if row:
            return dict(row)

    if user_location:
        query = text(
            """
            SELECT *
            FROM employee_poc_mapping
            WHERE LOWER(location) = LOWER(:location)
            ORDER BY id ASC
            LIMIT 1
            """
        )

        row = db.execute(
            query,
            {"location": user_location},
        ).mappings().first()

        if row:
            return dict(row)

    query = text(
        """
        SELECT *
        FROM employee_poc_mapping
        ORDER BY id ASC
        LIMIT 1
        """
    )

    row = db.execute(query).mappings().first()

    if row:
        return dict(row)

    return None


def format_single_poc_answer(mapping: dict | None, poc_type: str) -> str:
    if not mapping:
        return "I could not find a POC mapping for your profile."

    department = mapping.get("department")
    location = mapping.get("location")

    if poc_type == "hr":
        return (
            f"Your HR POC for {department} ({location}) is:\n"
            f"- Name: {mapping.get('hr_poc_name')}\n"
            f"- Email: {mapping.get('hr_poc_email')}"
        )

    if poc_type == "it":
        return (
            f"Your IT POC for {department} ({location}) is:\n"
            f"- Name: {mapping.get('it_poc_name')}\n"
            f"- Email: {mapping.get('it_poc_email')}"
        )

    if poc_type == "buddy":
        return (
            f"Your buddy contact for {department} ({location}) is:\n"
            f"- Name: {mapping.get('buddy_name')}\n"
            f"- Email: {mapping.get('buddy_email')}"
        )

    return (
        f"Here are your POC contacts for {department} ({location}):\n"
        f"- HR POC: {mapping.get('hr_poc_name')} ({mapping.get('hr_poc_email')})\n"
        f"- IT POC: {mapping.get('it_poc_name')} ({mapping.get('it_poc_email')})\n"
        f"- Buddy: {mapping.get('buddy_name')} ({mapping.get('buddy_email')})"
    )


def answer_poc_question(
    db: Session,
    query: str,
    current_user: User,
) -> tuple[str, int]:
    poc_type = detect_requested_poc_type(query)
    requested_department = detect_requested_department(query)

    mapping = get_relevant_poc_mapping(
        db=db,
        current_user=current_user,
        requested_department=requested_department,
    )

    answer = format_single_poc_answer(
        mapping=mapping,
        poc_type=poc_type,
    )

    return answer, 1 if mapping else 0