import hashlib
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Document


ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".csv",
    ".xlsx",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
}


ALLOWED_CONTENT_TYPES = {
    ".pdf": {
        "application/pdf",
        "application/octet-stream",
    },
    ".txt": {
        "text/plain",
        "application/octet-stream",
    },
    ".csv": {
        "text/csv",
        "application/csv",
        "application/vnd.ms-excel",
        "text/plain",
        "application/octet-stream",
    },
    ".xlsx": {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/octet-stream",
    },
    ".png": {
        "image/png",
        "application/octet-stream",
    },
    ".jpg": {
        "image/jpeg",
        "application/octet-stream",
    },
    ".jpeg": {
        "image/jpeg",
        "application/octet-stream",
    },
    ".tif": {
        "image/tiff",
        "application/octet-stream",
    },
    ".tiff": {
        "image/tiff",
        "application/octet-stream",
    },
}


@dataclass
class StoredUpload:
    original_file_name: str
    safe_original_file_name: str
    stored_file_name: str
    file_path: Path
    file_extension: str
    content_type: str | None
    size_bytes: int
    sha256: str


def sanitize_file_name(file_name: str) -> str:
    """
    Removes path traversal and unsafe characters.

    Example:
    ../../secret.pdf -> secret.pdf
    """
    base_name = Path(file_name or "").name.strip()

    if not base_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid file name.",
        )

    base_name = base_name.replace("\x00", "")
    base_name = re.sub(r"[^A-Za-z0-9._ -]", "_", base_name)
    base_name = re.sub(r"\s+", "_", base_name)

    if base_name in {".", ".."}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file name is not valid.",
        )

    return base_name


def validate_extension(file_name: str) -> str:
    extension = Path(file_name).suffix.lower()

    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported file type. Allowed file types are: "
                f"{', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}"
            ),
        )

    return extension


def validate_content_type(extension: str, content_type: str | None) -> None:
    if not content_type:
        return

    allowed_types = ALLOWED_CONTENT_TYPES.get(extension, set())

    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid content type '{content_type}' for '{extension}' file. "
                f"Allowed content types are: {', '.join(sorted(allowed_types))}"
            ),
        )


def get_upload_directory() -> Path:
    upload_dir = Path(settings.app_upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    return upload_dir.resolve()


def get_quarantine_directory() -> Path:
    quarantine_dir = Path(settings.app_quarantine_dir)
    quarantine_dir.mkdir(parents=True, exist_ok=True)

    return quarantine_dir.resolve()


def build_stored_file_name(
    safe_original_file_name: str,
    user_id: int | None,
) -> str:
    original_path = Path(safe_original_file_name)
    extension = original_path.suffix.lower()
    stem = original_path.stem[:80]

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    unique_id = uuid4().hex[:12]

    return f"{timestamp}_{unique_id}_user_{user_id}_{stem}{extension}"


def ensure_path_inside_directory(file_path: Path, directory: Path) -> None:
    resolved_file_path = file_path.resolve()
    resolved_directory = directory.resolve()

    if resolved_directory not in resolved_file_path.parents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload path.",
        )


def validate_file_signature(file_path: Path, extension: str) -> None:
    """
    Basic magic-header validation using standard library only.

    This protects against obvious file spoofing, for example:
    malware.exe renamed as policy.pdf
    """
    with file_path.open("rb") as file:
        header = file.read(16)

    if extension == ".pdf" and not header.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF signature.",
        )

    if extension == ".xlsx" and not header.startswith(b"PK\x03\x04"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid XLSX signature.",
        )

    if extension == ".png" and not header.startswith(b"\x89PNG\r\n\x1a\n"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PNG signature.",
        )

    if extension in {".jpg", ".jpeg"} and not header.startswith(b"\xff\xd8\xff"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JPEG signature.",
        )

    if extension in {".tif", ".tiff"} and not (
        header.startswith(b"II*\x00") or header.startswith(b"MM\x00*")
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TIFF signature.",
        )

    if extension in {".txt", ".csv"}:
        with file_path.open("rb") as file:
            sample = file.read(4096)

        if b"\x00" in sample:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Text/CSV file appears to contain binary content.",
            )


def calculate_file_sha256(file_path: Path) -> str:
    hasher = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def store_upload_file_securely(
    file: UploadFile,
    upload_dir: Path,
    current_user_id: int | None,
) -> StoredUpload:
    safe_original_file_name = sanitize_file_name(file.filename or "")
    extension = validate_extension(safe_original_file_name)

    validate_content_type(
        extension=extension,
        content_type=file.content_type,
    )

    stored_file_name = build_stored_file_name(
        safe_original_file_name=safe_original_file_name,
        user_id=current_user_id,
    )

    file_path = upload_dir / stored_file_name
    ensure_path_inside_directory(
        file_path=file_path,
        directory=upload_dir,
    )

    max_upload_file_bytes = settings.max_upload_file_bytes
    size_bytes = 0

    try:
        with file_path.open("wb") as output_file:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                size_bytes += len(chunk)

                if size_bytes > max_upload_file_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=(
                            "Uploaded file is too large. "
                            f"Maximum allowed size is {max_upload_file_bytes} bytes."
                        ),
                    )

                output_file.write(chunk)

        if size_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        validate_file_signature(
            file_path=file_path,
            extension=extension,
        )

        sha256 = calculate_file_sha256(file_path)

        return StoredUpload(
            original_file_name=Path(file.filename or "").name,
            safe_original_file_name=safe_original_file_name,
            stored_file_name=stored_file_name,
            file_path=file_path,
            file_extension=extension,
            content_type=file.content_type,
            size_bytes=size_bytes,
            sha256=sha256,
        )

    except Exception:
        if file_path.exists():
            file_path.unlink(missing_ok=True)

        raise

    finally:
        file.file.close()


def find_duplicate_document_by_checksum(
    db: Session,
    sha256: str,
) -> Document | None:
    """
    Detect duplicates without requiring a new DB column.

    It calculates hash from existing uploaded file paths and compares with
    the new file's SHA-256.
    """
    documents = db.query(Document).all()

    for document in documents:
        existing_path = Path(document.file_path)

        if not existing_path.exists():
            continue

        try:
            existing_sha256 = calculate_file_sha256(existing_path)
        except Exception:
            continue

        if existing_sha256 == sha256:
            return document

    return None


def quarantine_file(
    file_path: Path,
    reason: str,
) -> Path | None:
    """
    Moves a suspicious file to quarantine storage.
    """
    if not file_path.exists():
        return None

    quarantine_dir = get_quarantine_directory()
    quarantined_file_path = quarantine_dir / file_path.name

    counter = 1

    while quarantined_file_path.exists():
        quarantined_file_path = quarantine_dir / f"{file_path.stem}_{counter}{file_path.suffix}"
        counter += 1

    shutil.move(
        str(file_path),
        str(quarantined_file_path),
    )

    reason_path = quarantined_file_path.with_suffix(
        quarantined_file_path.suffix + ".reason.txt"
    )
    reason_path.write_text(reason, encoding="utf-8")

    return quarantined_file_path


def build_upload_security_metadata(stored_upload: StoredUpload) -> dict:
    return {
        "safe_original_file_name": stored_upload.safe_original_file_name,
        "stored_file_name": stored_upload.stored_file_name,
        "file_extension": stored_upload.file_extension,
        "content_type": stored_upload.content_type,
        "size_bytes": stored_upload.size_bytes,
        "sha256": stored_upload.sha256,
        "upload_security_validated": True,
        "validation_checks": [
            "safe_filename",
            "extension_allowlist",
            "content_type_check",
            "file_size_limit",
            "magic_header_check",
            "sha256_checksum",
            "path_traversal_protection",
        ],
    }