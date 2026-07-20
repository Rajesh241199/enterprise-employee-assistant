from datetime import date

from sqlalchemy import func

from app.db.models import (
    Department,
    EmployeeOnboardingProfile,
    EmployeePOCMapping,
    User,
)
from app.db.session import SessionLocal


EMPLOYEE_EMAIL = (
    "rajesh.employee@company.com"
)


def seed_onboarding_profile() -> None:
    db = SessionLocal()

    try:
        employee = (
            db.query(User)
            .filter(
                func.lower(User.email)
                == EMPLOYEE_EMAIL.lower()
            )
            .first()
        )

        if not employee:
            raise RuntimeError(
                "Employee account not found: "
                f"{EMPLOYEE_EMAIL}"
            )

        department = (
            db.query(Department)
            .filter(
                func.lower(Department.name)
                == "data science"
            )
            .first()
        )

        if not department:
            department = Department(
                name="Data Science",
                description=(
                    "Data Science, AI and "
                    "advanced analytics."
                ),
            )

            db.add(department)
            db.flush()

        employee.department = department
        employee.location = "Bengaluru"
        employee.designation = (
            "Data Scientist"
        )

        profile = (
            db.query(
                EmployeeOnboardingProfile
            )
            .filter(
                EmployeeOnboardingProfile.user_id
                == employee.id
            )
            .first()
        )

        if not profile:
            profile = (
                EmployeeOnboardingProfile(
                    user_id=employee.id,
                )
            )

            db.add(profile)

        profile.business_unit = (
            "Digital & AI"
        )

        profile.manager_name = (
            "Arjun Kumar"
        )

        profile.manager_email = (
            "arjun.kumar@company.com"
        )

        profile.project_name = (
            "Enterprise Employee Assistant"
        )

        profile.project_role = (
            "Data Scientist"
        )

        profile.project_start_date = date(
            2026,
            8,
            1,
        )

        profile.buddy_name = (
            "Ananya Singh"
        )

        profile.buddy_email = (
            "ananya.singh@company.com"
        )

        profile.onboarding_status = (
            "assigned"
        )

        poc_mapping = (
            db.query(EmployeePOCMapping)
            .filter(
                func.lower(
                    EmployeePOCMapping.department
                )
                == "data science",
                func.lower(
                    func.coalesce(
                        EmployeePOCMapping.location,
                        "",
                    )
                )
                == "bengaluru",
            )
            .first()
        )

        if not poc_mapping:
            poc_mapping = (
                EmployeePOCMapping(
                    department=(
                        "Data Science"
                    ),
                    location="Bengaluru",
                )
            )

            db.add(poc_mapping)

        poc_mapping.hr_poc_name = (
            "Priya Sharma"
        )

        poc_mapping.hr_poc_email = (
            "priya.hr@company.com"
        )

        poc_mapping.it_poc_name = (
            "Karthik Rao"
        )

        poc_mapping.it_poc_email = (
            "karthik.it@company.com"
        )

        db.commit()

        print(
            "Employee onboarding profile "
            "seeded successfully."
        )

        print(
            f"Employee: {employee.email}"
        )

        print(
            "Department: Data Science"
        )

        print(
            "Business Unit: Digital & AI"
        )

        print(
            "Project: Enterprise Employee "
            "Assistant"
        )

        print(
            "Buddy: Ananya Singh"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_onboarding_profile()