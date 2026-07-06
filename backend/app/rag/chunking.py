from dataclasses import dataclass, field
from typing import Any


@dataclass
class TextChunk:
    text: str
    chunk_index: int
    page_number: int | None = None
    section_title: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def split_text_into_chunks(
    text: str,
    chunk_size: int = 1200,
    chunk_overlap: int = 200,
    page_number: int | None = None,
    section_title: str | None = None,
    start_index: int = 0,
    metadata: dict[str, Any] | None = None,
) -> list[TextChunk]:
    cleaned_text = " ".join(text.split())

    if not cleaned_text:
        return []

    chunks: list[TextChunk] = []
    start = 0
    chunk_index = start_index

    while start < len(cleaned_text):
        end = start + chunk_size
        chunk_text = cleaned_text[start:end].strip()

        if chunk_text:
            chunks.append(
                TextChunk(
                    text=chunk_text,
                    chunk_index=chunk_index,
                    page_number=page_number,
                    section_title=section_title,
                    metadata=metadata or {},
                )
            )
            chunk_index += 1

        start = end - chunk_overlap

        if start < 0:
            start = 0

        if start >= len(cleaned_text):
            break

    return chunks