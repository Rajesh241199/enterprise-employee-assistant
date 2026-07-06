from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import require_authenticated_user
from app.db.models import Department, User
from app.db.session import get_db


router = APIRouter()


@router.get("/departments")
def get_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user),
):
    departments = db.query(Department).order_by(Department.name.asc()).all()

    return [
        {
            "id": department.id,
            "name": department.name,
            "description": department.description,
        }
        for department in departments
    ]