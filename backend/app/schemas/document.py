from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    file_name: str
    document_type: str
    policy_name: str | None = None
    department_owner: str | None = None
    access_level: str
    status: str
    uploaded_by: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True