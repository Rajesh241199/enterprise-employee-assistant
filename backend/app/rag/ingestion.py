from pathlib import Path
from typing import Any
from uuid import uuid4

import fitz
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
from qdrant_client.http.models import PointStruct
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Document, DocumentChunk, DocumentStatus
from app.rag.chunking import TextChunk, split_text_into_chunks
from app.rag.embeddings import embed_texts
from app.rag.retrieval import (
    delete_points_from_qdrant,
    ensure_qdrant_collection,
    upsert_chunks_to_qdrant,
)


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def configure_tesseract() -> None:
    if settings.tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def normalize_cell_value(value: Any) -> str:
    if value is None:
        return ""

    value_as_text = str(value).strip()

    if value_as_text.lower() in {"nan", "none", "nat"}:
        return ""

    return value_as_text


def should_apply_ocr(text: str) -> bool:
    if not settings.ocr_enabled:
        return False

    cleaned_text = " ".join(text.split())

    return len(cleaned_text) < settings.ocr_min_text_chars_per_page


def render_pdf_page_to_image(page: fitz.Page) -> Image.Image:
    zoom = settings.ocr_dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    pixmap = page.get_pixmap(matrix=matrix, alpha=False)

    image = Image.frombytes(
        "RGB",
        (pixmap.width, pixmap.height),
        pixmap.samples,
    )

    return image


def ocr_image(image: Image.Image) -> str:
    configure_tesseract()

    text = pytesseract.image_to_string(
        image,
        lang=settings.ocr_language,
    )

    return text or ""


def dataframe_to_table_chunks(
    dataframe: pd.DataFrame,
    source_name: str,
    start_index: int,
    page_number: int | None = None,
    sheet_name: str | None = None,
    table_name: str | None = None,
) -> list[TextChunk]:
    chunks: list[TextChunk] = []

    dataframe = dataframe.dropna(how="all")

    if dataframe.empty:
        return chunks

    dataframe = dataframe.fillna("")

    headers = [normalize_cell_value(column) for column in dataframe.columns]

    meaningful_headers = [
        header
        for header in headers
        if header and not header.lower().startswith("unnamed")
    ]

    # Avoid treating broken PDF layout text as a real table.
    if len(meaningful_headers) < 2:
        return chunks

    pending_row_text: str | None = None
    pending_metadata: dict[str, Any] | None = None

    for row_position, (_, row) in enumerate(dataframe.iterrows(), start=1):
        row_values = [normalize_cell_value(value) for value in row.tolist()]
        non_empty_values = [value for value in row_values if value]

        if not non_empty_values:
            continue

        # Continuation row caused by wrapped PDF text.
        # Attach it to the previous meaningful row instead of creating noisy chunks.
        if len(non_empty_values) == 1 and pending_row_text:
            pending_row_text = f"{pending_row_text} {non_empty_values[0]}"
            continue

        # Skip weak one-cell rows.
        if len(non_empty_values) < 2:
            continue

        # Save previous pending row before starting a new one.
        if pending_row_text:
            chunks.append(
                TextChunk(
                    text=pending_row_text,
                    chunk_index=start_index + len(chunks),
                    page_number=page_number,
                    section_title=table_name or sheet_name or "table",
                    metadata=pending_metadata or {},
                )
            )

        row_parts = []

        for header, value in zip(headers, row_values):
            clean_header = header or "Column"
            clean_value = normalize_cell_value(value)

            if clean_value:
                row_parts.append(f"{clean_header}: {clean_value}")

        if not row_parts:
            pending_row_text = None
            pending_metadata = None
            continue

        pending_row_text = (
            f"Table row from {source_name}. "
            f"{'Sheet: ' + sheet_name + '. ' if sheet_name else ''}"
            f"{'Table: ' + table_name + '. ' if table_name else ''}"
            f"Row {row_position}: "
            + "; ".join(row_parts)
        )

        pending_metadata = {
            "chunk_type": "table_row",
            "source_name": source_name,
            "sheet_name": sheet_name,
            "table_name": table_name,
            "row_position": row_position,
            "extractor": "table_aware",
            "ocr_applied": False,
        }

    # Save final pending row.
    if pending_row_text:
        chunks.append(
            TextChunk(
                text=pending_row_text,
                chunk_index=start_index + len(chunks),
                page_number=page_number,
                section_title=table_name or sheet_name or "table",
                metadata=pending_metadata or {},
            )
        )

    return chunks


def extract_pdf_text_chunks(file_path: Path, start_index: int = 0) -> list[TextChunk]:
    pdf_document = fitz.open(str(file_path))

    all_chunks: list[TextChunk] = []
    next_chunk_index = start_index

    for page_index in range(pdf_document.page_count):
        page = pdf_document.load_page(page_index)

        page_text = page.get_text("text") or ""
        extractor = "pymupdf"
        ocr_applied = False

        if should_apply_ocr(page_text):
            page_image = render_pdf_page_to_image(page)
            ocr_text = ocr_image(page_image)

            if ocr_text.strip():
                page_text = ocr_text
                extractor = "tesseract_ocr"
                ocr_applied = True

        page_chunks = split_text_into_chunks(
            text=page_text,
            chunk_size=1200,
            chunk_overlap=200,
            page_number=page_index + 1,
            start_index=next_chunk_index,
            metadata={
                "chunk_type": "text",
                "extractor": extractor,
                "ocr_applied": ocr_applied,
            },
        )

        all_chunks.extend(page_chunks)
        next_chunk_index += len(page_chunks)

    pdf_document.close()

    return all_chunks


def extract_pdf_table_chunks(file_path: Path, start_index: int = 0) -> list[TextChunk]:
    all_chunks: list[TextChunk] = []
    next_chunk_index = start_index

    with pdfplumber.open(str(file_path)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables() or []

            for table_index, table in enumerate(tables, start=1):
                if not table or len(table) < 2:
                    continue

                headers = table[0]
                rows = table[1:]

                dataframe = pd.DataFrame(rows, columns=headers)

                table_chunks = dataframe_to_table_chunks(
                    dataframe=dataframe,
                    source_name=file_path.name,
                    start_index=next_chunk_index,
                    page_number=page_number,
                    table_name=f"pdf_table_{table_index}",
                )

                all_chunks.extend(table_chunks)
                next_chunk_index += len(table_chunks)

    return all_chunks


def extract_pdf_chunks(file_path: Path) -> list[TextChunk]:
    text_chunks = extract_pdf_text_chunks(
        file_path=file_path,
        start_index=0,
    )

    table_chunks = extract_pdf_table_chunks(
        file_path=file_path,
        start_index=len(text_chunks),
    )

    return text_chunks + table_chunks


def extract_txt_chunks(file_path: Path) -> list[TextChunk]:
    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = file_path.read_text(encoding="latin-1")

    return split_text_into_chunks(
        text=text,
        chunk_size=1200,
        chunk_overlap=200,
        page_number=None,
        start_index=0,
        metadata={
            "chunk_type": "text",
            "extractor": "txt_reader",
            "ocr_applied": False,
        },
    )


def extract_csv_chunks(file_path: Path) -> list[TextChunk]:
    dataframe = pd.read_csv(file_path)

    return dataframe_to_table_chunks(
        dataframe=dataframe,
        source_name=file_path.name,
        start_index=0,
        table_name="csv_table",
    )


def extract_excel_chunks(file_path: Path) -> list[TextChunk]:
    excel_file = pd.ExcelFile(file_path)
    all_chunks: list[TextChunk] = []
    next_chunk_index = 0

    for sheet_name in excel_file.sheet_names:
        dataframe = pd.read_excel(file_path, sheet_name=sheet_name)

        sheet_chunks = dataframe_to_table_chunks(
            dataframe=dataframe,
            source_name=file_path.name,
            start_index=next_chunk_index,
            sheet_name=sheet_name,
            table_name="excel_table",
        )

        all_chunks.extend(sheet_chunks)
        next_chunk_index += len(sheet_chunks)

    return all_chunks


def extract_image_chunks(file_path: Path) -> list[TextChunk]:
    configure_tesseract()

    image = Image.open(file_path)
    text = ocr_image(image)

    return split_text_into_chunks(
        text=text,
        chunk_size=1200,
        chunk_overlap=200,
        page_number=None,
        start_index=0,
        metadata={
            "chunk_type": "image_ocr",
            "extractor": "tesseract_ocr",
            "ocr_applied": True,
            "source_image": file_path.name,
        },
    )


def extract_chunks_from_document(document: Document) -> list[TextChunk]:
    file_path = Path(document.file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return extract_pdf_chunks(file_path)

    if extension == ".txt":
        return extract_txt_chunks(file_path)

    if extension == ".csv":
        return extract_csv_chunks(file_path)

    if extension == ".xlsx":
        return extract_excel_chunks(file_path)

    if extension in IMAGE_EXTENSIONS:
        return extract_image_chunks(file_path)

    raise ValueError(
        "Indexing currently supports PDF, TXT, CSV, XLSX, PNG, JPG, JPEG, TIF, and TIFF files. "
        f"Received: {extension}"
    )


def cleanup_existing_document_chunks(db: Session, document: Document) -> None:
    existing_chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == document.id)
        .all()
    )

    old_qdrant_point_ids = [
        chunk.qdrant_point_id
        for chunk in existing_chunks
        if chunk.qdrant_point_id
    ]

    if old_qdrant_point_ids:
        delete_points_from_qdrant(old_qdrant_point_ids)

    for chunk in existing_chunks:
        db.delete(chunk)

    db.flush()


def build_chunk_metadata(document: Document, chunk: TextChunk) -> dict:
    base_metadata = {
        "document_type": document.document_type,
        "policy_name": document.policy_name,
        "department_owner": document.department_owner,
        "access_level": document.access_level,
        "file_name": document.file_name,
        "page_number": chunk.page_number,
        "section_title": chunk.section_title,
    }

    return {
        **base_metadata,
        **chunk.metadata,
    }


def index_document(
    db: Session,
    document: Document,
    force_reindex: bool = False,
) -> dict:
    if document.status == DocumentStatus.INDEXED.value and not force_reindex:
        return {
            "document_id": document.id,
            "status": document.status,
            "message": "Document is already indexed. Use force_reindex=true to index again.",
            "chunks_created": 0,
        }

    try:
        ensure_qdrant_collection()

        if force_reindex:
            cleanup_existing_document_chunks(db=db, document=document)

        chunks = extract_chunks_from_document(document)

        if not chunks:
            document.status = DocumentStatus.FAILED.value
            db.commit()

            return {
                "document_id": document.id,
                "status": document.status,
                "message": "No text could be extracted from the document.",
                "chunks_created": 0,
            }

        chunk_texts = [chunk.text for chunk in chunks]
        vectors = embed_texts(chunk_texts)

        qdrant_points: list[PointStruct] = []

        for chunk, vector in zip(chunks, vectors):
            point_id = str(uuid4())
            metadata = build_chunk_metadata(document=document, chunk=chunk)

            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_text=chunk.text,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                section_title=chunk.section_title,
                qdrant_point_id=point_id,
                chunk_metadata=metadata,
            )

            db.add(db_chunk)

            qdrant_points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={
                        "document_id": document.id,
                        "file_name": document.file_name,
                        "document_type": document.document_type,
                        "policy_name": document.policy_name,
                        "department_owner": document.department_owner,
                        "access_level": document.access_level,
                        "chunk_index": chunk.chunk_index,
                        "page_number": chunk.page_number,
                        "section_title": chunk.section_title,
                        "text": chunk.text,
                        **chunk.metadata,
                    },
                )
            )

        upsert_chunks_to_qdrant(qdrant_points)

        document.status = DocumentStatus.INDEXED.value
        db.commit()

        return {
            "document_id": document.id,
            "status": document.status,
            "message": "Document indexed successfully with OCR fallback support.",
            "chunks_created": len(chunks),
        }

    except Exception as exc:
        db.rollback()

        document.status = DocumentStatus.FAILED.value
        db.add(document)
        db.commit()

        raise exc