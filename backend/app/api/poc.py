from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.permissions import require_authenticated_user
from app.db.models import EmployeePOCMapping, User
from app.db.session import get_db


router = APIRouter()


@router.get("/poc")
def get_poc_mapping(
    department: str = Query(..., description="Employee department"),
    location: str | None = Query(None, description="Employee location"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user),
):
    query = db.query(EmployeePOCMapping).filter(
        EmployeePOCMapping.department == department
    )

    if location:
        query = query.filter(EmployeePOCMapping.location == location)

    mapping = query.first()

    if not mapping:
        return {
            "found": False,
            "message": "No POC mapping found for the given department/location.",
            "poc": None,
        }

    return {
        "found": True,
        "department": mapping.department,
        "location": mapping.location,
        "poc": {
            "hr_poc": {
                "name": mapping.hr_poc_name,
                "email": mapping.hr_poc_email,
            },
            "it_poc": {
                "name": mapping.it_poc_name,
                "email": mapping.it_poc_email,
            },
            "buddy": {
                "name": mapping.buddy_name,
                "email": mapping.buddy_email,
            },
        },
    }