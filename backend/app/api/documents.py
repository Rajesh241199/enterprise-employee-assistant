from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.file_validation import (
    build_upload_security_metadata,
    find_duplicate_document_by_checksum,
    get_upload_directory,
    quarantine_file,
    store_upload_file_securely,
)
from app.core.permissions import require_authenticated_user
from app.db.models import Document, User
from app.db.session import get_db
from app.rag.ingestion import index_document


router = APIRouter()


ALLOWED_ACCESS_LEVELS = {
    "all_employees",
    "hr_only",
    "finance_only",
    "it_only",
    "leadership_only",
    "admin_only",
    "confidential",
}


DOCUMENT_ADMIN_ROLES = {
    "hr_admin",
    "finance_admin",
    "it_admin",
    "super_admin",
}


def normalize_role(role: object) -> str:
    if role is None:
        return "employee"

    raw_role = getattr(role, "value", role)
    normalized_role = str(raw_role).strip().lower()
    normalized_role = normalized_role.replace(" ", "_")
    normalized_role = normalized_role.replace("-", "_")

    return normalized_role


def ensure_document_admin_user(current_user: User) -> None:
    role = normalize_role(getattr(current_user, "role", None))

    if role not in DOCUMENT_ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage documents.",
        )


def validate_access_level(access_level: str) -> str:
    normalized_access_level = access_level.strip()

    if normalized_access_level not in ALLOWED_ACCESS_LEVELS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid access_level. Allowed values are: "
                f"{', '.join(sorted(ALLOWED_ACCESS_LEVELS))}"
            ),
        )

    return normalized_access_level


def validate_required_text_field(
    value: str,
    field_name: str,
    max_length: int = 255,
) -> str:
    cleaned_value = " ".join((value or "").split())

    if not cleaned_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} is required.",
        )

    if len(cleaned_value) > max_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{field_name} must not exceed {max_length} characters.",
        )

    return cleaned_value


def document_to_dict(document: Document) -> dict:
    return {
        "id": document.id,
        "file_name": document.file_name,
        "document_type": document.document_type,
        "policy_name": document.policy_name,
        "department_owner": document.department_owner,
        "access_level": document.access_level,
        "status": document.status,
        "uploaded_by": document.uploaded_by,
        "extra_metadata": document.extra_metadata,
        "created_at": (
            document.created_at.isoformat()
            if getattr(document, "created_at", None)
            else None
        ),
    }


@router.post("/documents/upload")
def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    policy_name: str = Form(...),
    department_owner: str = Form(...),
    access_level: str = Form(...),
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    ensure_document_admin_user(current_user)

    normalized_access_level = validate_access_level(access_level)

    cleaned_document_type = validate_required_text_field(
        value=document_type,
        field_name="document_type",
        max_length=100,
    )

    cleaned_policy_name = validate_required_text_field(
        value=policy_name,
        field_name="policy_name",
        max_length=255,
    )

    cleaned_department_owner = validate_required_text_field(
        value=department_owner,
        field_name="department_owner",
        max_length=100,
    )

    upload_dir = get_upload_directory()

    stored_upload = store_upload_file_securely(
        file=file,
        upload_dir=upload_dir,
        current_user_id=current_user.id,
    )

    duplicate_document = find_duplicate_document_by_checksum(
        db=db,
        sha256=stored_upload.sha256,
    )

    if duplicate_document:
        stored_upload.file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Duplicate document upload blocked.",
                "duplicate_document_id": duplicate_document.id,
                "duplicate_file_name": duplicate_document.file_name,
                "sha256": stored_upload.sha256,
            },
        )

    upload_security_metadata = build_upload_security_metadata(stored_upload)

    document = Document(
        file_name=stored_upload.safe_original_file_name,
        file_path=str(stored_upload.file_path),
        document_type=cleaned_document_type,
        policy_name=cleaned_policy_name,
        department_owner=cleaned_department_owner,
        access_level=normalized_access_level,
        status="uploaded",
        uploaded_by=current_user.id,
        extra_metadata={
            "upload_security": upload_security_metadata,
        },
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document_to_dict(document)


@router.get("/documents")
def list_documents(
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    ensure_document_admin_user(current_user)

    documents = (
        db.query(Document)
        .order_by(Document.id.asc())
        .all()
    )

    return [document_to_dict(document) for document in documents]


@router.post("/documents/{document_id}/index")
def index_uploaded_document(
    document_id: int,
    force_reindex: bool = False,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    ensure_document_admin_user(current_user)

    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id={document_id} was not found.",
        )

    if not Path(document.file_path).exists():
        document.status = "failed"
        db.add(document)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file was not found in storage.",
        )

    try:
        result = index_document(
            db=db,
            document=document,
            force_reindex=force_reindex,
        )

    except Exception as exc:
        reason = str(exc)
        reason_lower = reason.lower()

        is_validation_failure = (
            "security scan failed" in reason_lower
            or "domain validation failed" in reason_lower
        )

        if is_validation_failure:
            quarantined_path = quarantine_file(
                file_path=Path(document.file_path),
                reason=reason,
            )

            existing_metadata = dict(document.extra_metadata or {})
            existing_metadata["quarantine"] = {
                "quarantined": True,
                "quarantine_path": str(quarantined_path) if quarantined_path else None,
                "reason": reason[:1000],
            }

            document.status = "failed"
            document.extra_metadata = existing_metadata

            db.add(document)
            db.commit()
            db.refresh(document)

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Document failed validation and was quarantined.",
                    "document_id": document.id,
                    "reason": reason[:1000],
                    "quarantine_path": str(quarantined_path) if quarantined_path else None,
                },
            ) from exc

        raise

    document.status = "indexed"
    db.add(document)
    db.commit()
    db.refresh(document)

    if isinstance(result, dict):
        return {
            "document_id": document.id,
            "status": "indexed",
            **result,
        }

    return {
        "document_id": document.id,
        "status": "indexed",
        "message": "Document indexed successfully.",
    }