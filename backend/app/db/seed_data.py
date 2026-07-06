from datetime import date

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.models import (
    Department,
    EmployeePOCMapping,
    Event,
    Holiday,
    TaxSlab,
    User,
    UserRole,
)
from app.db.session import SessionLocal


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def seed_departments(db: Session) -> None:
    departments = [
        {"name": "Human Resources", "description": "Handles employee policies, onboarding, benefits, and HR operations."},
        {"name": "Finance", "description": "Handles payroll, tax, reimbursement, and finance policies."},
        {"name": "IT", "description": "Handles system access, devices, support, and security policies."},
        {"name": "Data Science", "description": "Builds data, AI, ML, and analytics solutions."},
    ]

    for dept in departments:
        existing = db.query(Department).filter(Department.name == dept["name"]).first()
        if not existing:
            db.add(Department(**dept))

    db.commit()


def seed_users(db: Session) -> None:
    hr_department = db.query(Department).filter(Department.name == "Human Resources").first()
    finance_department = db.query(Department).filter(Department.name == "Finance").first()
    ds_department = db.query(Department).filter(Department.name == "Data Science").first()

    users = [
        {
            "employee_id": "EMP001",
            "full_name": "Rajesh Kannan",
            "email": "rajesh.employee@company.com",
            "hashed_password": hash_password("Password@123"),
            "role": UserRole.EMPLOYEE.value,
            "location": "Bangalore",
            "designation": "Data Scientist",
            "department_id": ds_department.id if ds_department else None,
        },
        {
            "employee_id": "HR001",
            "full_name": "Priya Sharma",
            "email": "priya.hr@company.com",
            "hashed_password": hash_password("Password@123"),
            "role": UserRole.HR_ADMIN.value,
            "location": "Bangalore",
            "designation": "HR Manager",
            "department_id": hr_department.id if hr_department else None,
        },
        {
            "employee_id": "FIN001",
            "full_name": "Arun Kumar",
            "email": "arun.finance@company.com",
            "hashed_password": hash_password("Password@123"),
            "role": UserRole.FINANCE_ADMIN.value,
            "location": "Bangalore",
            "designation": "Finance Manager",
            "department_id": finance_department.id if finance_department else None,
        },
    ]

    for user in users:
        existing = db.query(User).filter(User.email == user["email"]).first()
        if not existing:
            db.add(User(**user))

    db.commit()


def seed_holidays(db: Session) -> None:
    holidays = [
        {
            "holiday_name": "Republic Day",
            "holiday_date": date(2026, 1, 26),
            "location": "India",
            "holiday_type": "national",
        },
        {
            "holiday_name": "Independence Day",
            "holiday_date": date(2026, 8, 15),
            "location": "India",
            "holiday_type": "national",
        },
        {
            "holiday_name": "Diwali",
            "holiday_date": date(2026, 11, 8),
            "location": "India",
            "holiday_type": "festival",
        },
    ]

    for holiday in holidays:
        existing = (
            db.query(Holiday)
            .filter(
                Holiday.holiday_name == holiday["holiday_name"],
                Holiday.holiday_date == holiday["holiday_date"],
            )
            .first()
        )
        if not existing:
            db.add(Holiday(**holiday))

    db.commit()


def seed_events(db: Session) -> None:
    events = [
        {
            "event_name": "AI Enablement Workshop",
            "description": "Internal workshop covering GenAI basics, RAG, and enterprise use cases.",
            "event_date": date(2026, 7, 15),
            "start_time": "15:00",
            "end_time": "17:00",
            "location": "Training Room 2",
            "organizer": "Data Science Team",
            "preparation_notes": "Bring your laptop and complete the GenAI pre-read document.",
            "event_metadata": {
                "event_type": "training",
                "audience": "all_employees",
            },
        },
        {
            "event_name": "Quarterly Townhall",
            "description": "Company-wide leadership update covering business performance, hiring plans, and upcoming initiatives.",
            "event_date": date(2026, 7, 30),
            "start_time": "10:00",
            "end_time": "11:30",
            "location": "Main Auditorium",
            "organizer": "Leadership Team",
            "preparation_notes": "Employees can submit questions in advance through the internal portal.",
            "event_metadata": {
                "event_type": "townhall",
                "audience": "all_employees",
            },
        },
    ]

    for event in events:
        existing = (
            db.query(Event)
            .filter(
                Event.event_name == event["event_name"],
                Event.event_date == event["event_date"],
            )
            .first()
        )
        if not existing:
            db.add(Event(**event))

    db.commit()


def seed_poc_mappings(db: Session) -> None:
    mappings = [
        {
            "department": "Data Science",
            "location": "Bangalore",
            "hr_poc_name": "Priya Sharma",
            "hr_poc_email": "priya.hr@company.com",
            "it_poc_name": "Karthik Menon",
            "it_poc_email": "karthik.it@company.com",
            "buddy_name": "Arjun Nair",
            "buddy_email": "arjun.ds@company.com",
        },
        {
            "department": "Finance",
            "location": "Bangalore",
            "hr_poc_name": "Priya Sharma",
            "hr_poc_email": "priya.hr@company.com",
            "it_poc_name": "Karthik Menon",
            "it_poc_email": "karthik.it@company.com",
            "buddy_name": "Meera Iyer",
            "buddy_email": "meera.finance@company.com",
        },
    ]

    for mapping in mappings:
        existing = (
            db.query(EmployeePOCMapping)
            .filter(
                EmployeePOCMapping.department == mapping["department"],
                EmployeePOCMapping.location == mapping["location"],
            )
            .first()
        )
        if not existing:
            db.add(EmployeePOCMapping(**mapping))

    db.commit()


def seed_tax_slabs(db: Session) -> None:
    """
    Sample tax slabs for development/testing only.
    Replace with verified current tax rules before using this in a real payroll/tax setting.
    """

    slabs = [
        {
            "financial_year": "2026-27",
            "regime": "sample_new_regime",
            "min_income": 0,
            "max_income": 300000,
            "tax_rate": 0.0,
            "notes": "Sample data only.",
        },
        {
            "financial_year": "2026-27",
            "regime": "sample_new_regime",
            "min_income": 300001,
            "max_income": 700000,
            "tax_rate": 0.05,
            "notes": "Sample data only.",
        },
        {
            "financial_year": "2026-27",
            "regime": "sample_new_regime",
            "min_income": 700001,
            "max_income": 1000000,
            "tax_rate": 0.10,
            "notes": "Sample data only.",
        },
        {
            "financial_year": "2026-27",
            "regime": "sample_old_regime",
            "min_income": 0,
            "max_income": 250000,
            "tax_rate": 0.0,
            "notes": "Sample data only.",
        },
        {
            "financial_year": "2026-27",
            "regime": "sample_old_regime",
            "min_income": 250001,
            "max_income": 500000,
            "tax_rate": 0.05,
            "notes": "Sample data only.",
        },
        {
            "financial_year": "2026-27",
            "regime": "sample_old_regime",
            "min_income": 500001,
            "max_income": 1000000,
            "tax_rate": 0.20,
            "notes": "Sample data only.",
        },
    ]

    for slab in slabs:
        existing = (
            db.query(TaxSlab)
            .filter(
                TaxSlab.financial_year == slab["financial_year"],
                TaxSlab.regime == slab["regime"],
                TaxSlab.min_income == slab["min_income"],
                TaxSlab.max_income == slab["max_income"],
            )
            .first()
        )
        if not existing:
            db.add(TaxSlab(**slab))

    db.commit()


def seed_all() -> None:
    db = SessionLocal()

    try:
        print("Seeding departments...")
        seed_departments(db)

        print("Seeding users...")
        seed_users(db)

        print("Seeding holidays...")
        seed_holidays(db)

        print("Seeding events...")
        seed_events(db)

        print("Seeding POC mappings...")
        seed_poc_mappings(db)

        print("Seeding sample tax slabs...")
        seed_tax_slabs(db)

        print("Seed data inserted successfully.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_all()