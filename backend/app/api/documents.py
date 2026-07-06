import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from qdrant_client import QdrantClient, models
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.permissions import require_authenticated_user
from app.db.models import Document, DocumentChunk, User
from app.db.session import get_db
from app.rag.ingestion import index_document


router = APIRouter()


ALLOWED_DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
}


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


def get_upload_directory() -> Path:
    upload_dir = Path(settings.app_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    return upload_dir


def validate_uploaded_file(file: UploadFile) -> str:
    original_file_name = Path(file.filename or "").name

    if not original_file_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid file name.",
        )

    file_extension = Path(original_file_name).suffix.lower()

    if file_extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported file type. Allowed file types are: "
                f"{', '.join(sorted(ALLOWED_DOCUMENT_EXTENSIONS))}"
            ),
        )

    return original_file_name


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
        "created_at": (
            document.created_at.isoformat()
            if getattr(document, "created_at", None)
            else None
        ),
    }


def delete_qdrant_points_for_document(document_id: int) -> None:
    client = QdrantClient(
        host=settings.qdrant_host,
        port=int(settings.qdrant_port),
    )

    try:
        client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id),
                        )
                    ]
                )
            ),
        )

    except Exception:
        # Safe fallback:
        # If the collection does not exist yet or Qdrant has no points,
        # indexing can still continue.
        return


def clear_existing_document_index(db: Session, document_id: int) -> None:
    db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).delete(synchronize_session=False)

    db.commit()

    delete_qdrant_points_for_document(document_id=document_id)


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

    original_file_name = validate_uploaded_file(file)
    normalized_access_level = validate_access_level(access_level)

    upload_dir = get_upload_directory()

    stored_file_name = f"{Path(original_file_name).stem}_{current_user.id}{Path(original_file_name).suffix}"
    file_path = upload_dir / stored_file_name

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document = Document(
        file_name=original_file_name,
        file_path=str(file_path),
        document_type=document_type.strip(),
        policy_name=policy_name.strip(),
        department_owner=department_owner.strip(),
        access_level=normalized_access_level,
        status="uploaded",
        uploaded_by=current_user.id,
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

    if force_reindex:
        clear_existing_document_index(
            db=db,
            document_id=document_id,
        )

    result = index_document(
        db=db,
        document=document,
    )

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