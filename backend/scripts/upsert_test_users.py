import sys
from pathlib import Path

# Make backend/app imports work when running:
# python scripts/upsert_test_users.py
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_ROOT))

from app.db.session import SessionLocal
from app.db.models import User

try:
    from app.db.models import Department
except ImportError:
    Department = None

try:
    from app.core.security import get_password_hash
except ImportError:
    from app.core.security import hash_password as get_password_hash


TEST_USERS = [
    {
        "employee_id": "EMP001",
        "full_name": "Rajesh Kannan",
        "email": "rajesh.employee@company.com",
        "password": "Password@123",
        "role": "employee",
        "department_name": "Data Science",
        "location": "Bangalore",
        "designation": "Data Scientist",
    },
    {
        "employee_id": "EMP002",
        "full_name": "Priya Sharma",
        "email": "priya.hr@company.com",
        "password": "Password@123",
        "role": "hr_admin",
        "department_name": "Human Resources",
        "location": "Bangalore",
        "designation": "HR Manager",
    },
    {
        "employee_id": "EMP003",
        "full_name": "Meera Iyer",
        "email": "meera.finance@company.com",
        "password": "Password@123",
        "role": "finance_admin",
        "department_name": "Finance",
        "location": "Bangalore",
        "designation": "Finance Manager",
    },
    {
        "employee_id": "EMP004",
        "full_name": "Karthik Menon",
        "email": "karthik.it@company.com",
        "password": "Password@123",
        "role": "it_admin",
        "department_name": "IT",
        "location": "Bangalore",
        "designation": "IT Manager",
    },
]


def model_has_column(model, column_name: str) -> bool:
    return column_name in model.__table__.columns


def set_if_column_exists(instance, column_name: str, value) -> None:
    if model_has_column(instance.__class__, column_name):
        setattr(instance, column_name, value)


def get_role_value_for_model(role: str):
    role_column = User.__table__.columns.get("role")
    enum_class = getattr(role_column.type, "enum_class", None) if role_column is not None else None

    if enum_class:
        for enum_member in enum_class:
            enum_value = str(enum_member.value).strip().lower()
            enum_name = str(enum_member.name).strip().lower()

            if enum_value == role or enum_name == role:
                return enum_member

    return role


def get_department_name_column() -> str | None:
    if Department is None:
        return None

    possible_columns = ["name", "department_name", "title"]

    for column_name in possible_columns:
        if model_has_column(Department, column_name):
            return column_name

    return None


def get_or_create_department(db, department_name: str):
    if Department is None:
        return None

    department_name_column = get_department_name_column()

    if department_name_column is None:
        return None

    department = (
        db.query(Department)
        .filter(getattr(Department, department_name_column) == department_name)
        .first()
    )

    if department:
        return department

    department = Department()
    setattr(department, department_name_column, department_name)

    if model_has_column(Department, "description"):
        department.description = f"{department_name} department"

    db.add(department)
    db.flush()

    return department


def set_department(db, user: User, department_name: str) -> None:
    if model_has_column(User, "department"):
        user.department = department_name
        return

    if model_has_column(User, "department_id"):
        department = get_or_create_department(db, department_name)

        if department:
            user.department_id = department.id

        return


def set_password(user: User, plain_password: str) -> None:
    hashed_password = get_password_hash(plain_password)

    if model_has_column(User, "hashed_password"):
        user.hashed_password = hashed_password
        return

    if model_has_column(User, "password_hash"):
        user.password_hash = hashed_password
        return

    raise RuntimeError(
        "No password column found on User model. "
        "Expected 'hashed_password' or 'password_hash'."
    )


def upsert_user(db, user_data: dict) -> User:
    user = (
        db.query(User)
        .filter(User.email == user_data["email"])
        .first()
    )

    if not user:
        user = User()
        db.add(user)

    set_if_column_exists(user, "employee_id", user_data["employee_id"])
    set_if_column_exists(user, "full_name", user_data["full_name"])
    set_if_column_exists(user, "name", user_data["full_name"])
    set_if_column_exists(user, "email", user_data["email"])
    set_if_column_exists(user, "role", get_role_value_for_model(user_data["role"]))
    set_if_column_exists(user, "location", user_data["location"])
    set_if_column_exists(user, "designation", user_data["designation"])
    set_if_column_exists(user, "job_title", user_data["designation"])
    set_if_column_exists(user, "is_active", True)

    # Set password before department because department creation may call db.flush().
    # If db.flush() happens before password is set, PostgreSQL rejects the user row
    # because hashed_password is NOT NULL.
    set_password(
        user=user,
        plain_password=user_data["password"],
    )

    set_department(
        db=db,
        user=user,
        department_name=user_data["department_name"],
    )

    return user


def main() -> None:
    db = SessionLocal()

    try:
        for user_data in TEST_USERS:
            upsert_user(db, user_data)
            print(f"Upserted user: {user_data['email']}")

        db.commit()
        print("All test users created/updated successfully.")

    except Exception as exc:
        db.rollback()
        print(f"Failed to upsert test users: {exc}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()