from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import (
    Department,
    EmployeeOnboardingProfile,
    EmployeePOCMapping,
    User,
    UserRole,
)
from app.schemas.admin_onboarding import (
    AdminEmployeeOnboardingCreate,
    AdminEmployeeOnboardingListResponse,
    AdminEmployeeOnboardingResponse,
    AdminEmployeeOnboardingUpdate,
)
from app.services.onboarding_service import (
    build_onboarding_profile,
)


SHARED_POC_FIELDS = {
    "hr_poc_name",
    "hr_poc_email",
    "it_poc_name",
    "it_poc_email",
}


def normalize_email(
    email: str,
) -> str:
    return email.strip().lower()


def get_employee_or_404(
    db: Session,
    user_id: int,
) -> User:
    employee = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail="Employee not found.",
        )

    return employee


def ensure_unique_employee_fields(
    db: Session,
    employee_id: str,
    email: str,
    exclude_user_id: int | None = None,
) -> None:
    employee_query = (
        db.query(User)
        .filter(
            func.lower(User.employee_id)
            == employee_id.lower()
        )
    )

    email_query = (
        db.query(User)
        .filter(
            func.lower(User.email)
            == email.lower()
        )
    )

    if exclude_user_id is not None:
        employee_query = (
            employee_query.filter(
                User.id != exclude_user_id
            )
        )

        email_query = (
            email_query.filter(
                User.id != exclude_user_id
            )
        )

    if employee_query.first():
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "An employee with this "
                "employee ID already exists."
            ),
        )

    if email_query.first():
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "An employee with this "
                "email already exists."
            ),
        )


def get_or_create_department(
    db: Session,
    department_name: str,
) -> Department:
    normalized_name = (
        department_name.strip()
    )

    department = (
        db.query(Department)
        .filter(
            func.lower(Department.name)
            == normalized_name.lower()
        )
        .first()
    )

    if department:
        return department

    department = Department(
        name=normalized_name,
        description=(
            f"{normalized_name} department."
        ),
    )

    db.add(department)
    db.flush()

    return department


def get_or_create_onboarding_profile(
    db: Session,
    employee: User,
) -> EmployeeOnboardingProfile:
    profile = (
        db.query(EmployeeOnboardingProfile)
        .filter(
            EmployeeOnboardingProfile.user_id
            == employee.id
        )
        .first()
    )

    if profile:
        return profile

    profile = EmployeeOnboardingProfile(
        user_id=employee.id,
        onboarding_status="not_assigned",
    )

    db.add(profile)
    db.flush()

    return profile


def upsert_poc_mapping(
    db: Session,
    department: str,
    location: str,
    poc_values: dict,
) -> None:
    provided_values = {
        key: value
        for key, value
        in poc_values.items()
        if (
            key in SHARED_POC_FIELDS
            and value is not None
        )
    }

    if not provided_values:
        return

    mapping = (
        db.query(EmployeePOCMapping)
        .filter(
            func.lower(
                EmployeePOCMapping.department
            )
            == department.lower(),
            func.lower(
                func.coalesce(
                    EmployeePOCMapping.location,
                    "",
                )
            )
            == location.lower(),
        )
        .first()
    )

    if not mapping:
        mapping = EmployeePOCMapping(
            department=department,
            location=location,
        )

        db.add(mapping)
        db.flush()

    for field_name, field_value in (
        provided_values.items()
    ):
        setattr(
            mapping,
            field_name,
            str(field_value).strip(),
        )


def build_admin_employee_response(
    db: Session,
    employee: User,
) -> AdminEmployeeOnboardingResponse:
    onboarding_profile = (
        build_onboarding_profile(
            db=db,
            current_user=employee,
        )
    )

    return AdminEmployeeOnboardingResponse(
        user_id=employee.id,
        is_active=employee.is_active,
        role=str(employee.role),
        **onboarding_profile.model_dump(),
    )


def create_employee_onboarding(
    db: Session,
    payload: AdminEmployeeOnboardingCreate,
) -> AdminEmployeeOnboardingResponse:
    normalized_email = normalize_email(
        str(payload.email)
    )

    ensure_unique_employee_fields(
        db=db,
        employee_id=payload.employee_id,
        email=normalized_email,
    )

    try:
        department = get_or_create_department(
            db=db,
            department_name=(
                payload.department
            ),
        )

        employee = User(
            employee_id=payload.employee_id,
            full_name=payload.full_name,
            email=normalized_email,
            hashed_password=hash_password(
                payload.temporary_password
            ),
            role=UserRole.EMPLOYEE.value,
            location=payload.location,
            designation=payload.designation,
            department=department,
            is_active=payload.is_active,
        )

        db.add(employee)
        db.flush()

        profile = EmployeeOnboardingProfile(
            user_id=employee.id,
            business_unit=(
                payload.business_unit
            ),
            manager_name=(
                payload.manager_name
            ),
            manager_email=(
                str(payload.manager_email)
                if payload.manager_email
                else None
            ),
            project_name=(
                payload.project_name
            ),
            project_role=(
                payload.project_role
            ),
            project_start_date=(
                payload.project_start_date
            ),
            buddy_name=(
                payload.buddy_name
            ),
            buddy_email=(
                str(payload.buddy_email)
                if payload.buddy_email
                else None
            ),
            onboarding_status=(
                payload.onboarding_status
            ),
        )

        db.add(profile)

        upsert_poc_mapping(
            db=db,
            department=payload.department,
            location=payload.location,
            poc_values={
                "hr_poc_name": (
                    payload.hr_poc_name
                ),
                "hr_poc_email": (
                    str(payload.hr_poc_email)
                    if payload.hr_poc_email
                    else None
                ),
                "it_poc_name": (
                    payload.it_poc_name
                ),
                "it_poc_email": (
                    str(payload.it_poc_email)
                    if payload.it_poc_email
                    else None
                ),
            },
        )

        db.commit()
        db.refresh(employee)

        return build_admin_employee_response(
            db=db,
            employee=employee,
        )

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Employee onboarding record "
                "could not be created because "
                "a unique value already exists."
            ),
        ) from exc

    except Exception:
        db.rollback()
        raise


def update_employee_onboarding(
    db: Session,
    user_id: int,
    payload: AdminEmployeeOnboardingUpdate,
) -> AdminEmployeeOnboardingResponse:
    employee = get_employee_or_404(
        db=db,
        user_id=user_id,
    )

    update_values = payload.model_dump(
        exclude_unset=True
    )

    requested_employee_id = (
        update_values.get("employee_id")
    )

    new_employee_id = (
        requested_employee_id
        or employee.employee_id
    )

    requested_email = (
        update_values.get("email")
    )

    new_email = normalize_email(
        str(
            requested_email
            or employee.email
        )
    )

    ensure_unique_employee_fields(
        db=db,
        employee_id=new_employee_id,
        email=new_email,
        exclude_user_id=employee.id,
    )

    try:
        if requested_employee_id:
            employee.employee_id = (
                requested_employee_id
            )

        if update_values.get("full_name"):
            employee.full_name = (
                update_values["full_name"]
            )

        if requested_email:
            employee.email = new_email

        if "designation" in update_values:
            employee.designation = (
                update_values["designation"]
            )

        if update_values.get("location"):
            employee.location = (
                update_values["location"]
            )

        if "is_active" in update_values:
            employee.is_active = (
                update_values["is_active"]
            )

        new_password = update_values.get(
            "new_temporary_password"
        )

        if new_password:
            employee.hashed_password = (
                hash_password(new_password)
            )

        requested_department = (
            update_values.get("department")
        )

        if requested_department:
            employee.department = (
                get_or_create_department(
                    db=db,
                    department_name=(
                        requested_department
                    ),
                )
            )

        profile = (
            get_or_create_onboarding_profile(
                db=db,
                employee=employee,
            )
        )

        profile_field_map = {
            "business_unit": (
                "business_unit"
            ),
            "manager_name": (
                "manager_name"
            ),
            "manager_email": (
                "manager_email"
            ),
            "project_name": (
                "project_name"
            ),
            "project_role": (
                "project_role"
            ),
            "project_start_date": (
                "project_start_date"
            ),
            "buddy_name": (
                "buddy_name"
            ),
            "buddy_email": (
                "buddy_email"
            ),
            "onboarding_status": (
                "onboarding_status"
            ),
        }

        for request_field, model_field in (
            profile_field_map.items()
        ):
            if request_field not in update_values:
                continue

            field_value = update_values[
                request_field
            ]

            if (
                request_field
                in {
                    "manager_email",
                    "buddy_email",
                }
                and field_value is not None
            ):
                field_value = str(
                    field_value
                )

            setattr(
                profile,
                model_field,
                field_value,
            )

        poc_values = {}

        for field_name in SHARED_POC_FIELDS:
            if field_name not in update_values:
                continue

            field_value = update_values[
                field_name
            ]

            if (
                field_name.endswith("_email")
                and field_value is not None
            ):
                field_value = str(
                    field_value
                )

            poc_values[field_name] = (
                field_value
            )

        department_name = (
            employee.department.name
            if employee.department
            else None
        )

        if (
            department_name
            and employee.location
            and poc_values
        ):
            upsert_poc_mapping(
                db=db,
                department=department_name,
                location=employee.location,
                poc_values=poc_values,
            )

        db.commit()
        db.refresh(employee)

        return build_admin_employee_response(
            db=db,
            employee=employee,
        )

    except HTTPException:
        db.rollback()
        raise

    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=(
                "Employee onboarding record "
                "could not be updated because "
                "a unique value already exists."
            ),
        ) from exc

    except Exception:
        db.rollback()
        raise


def list_employee_onboarding_records(
    db: Session,
    offset: int,
    limit: int,
) -> AdminEmployeeOnboardingListResponse:
    base_query = (
        db.query(User)
        .filter(
            User.role
            == UserRole.EMPLOYEE.value
        )
    )

    total = base_query.count()

    employees = (
        base_query
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = [
        build_admin_employee_response(
            db=db,
            employee=employee,
        )
        for employee in employees
    ]

    return (
        AdminEmployeeOnboardingListResponse(
            items=items,
            total=total,
            offset=offset,
            limit=limit,
        )
    )