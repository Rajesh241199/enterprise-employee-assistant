from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointIdsList,
    PointStruct,
    VectorParams,
)

from app.core.config import settings
from app.rag.embeddings import embed_text, get_embedding_dimension


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
    )


def check_qdrant_connection() -> bool:
    try:
        client = get_qdrant_client()
        client.get_collections()
        return True
    except Exception:
        return False


def ensure_qdrant_collection() -> None:
    client = get_qdrant_client()

    collections = client.get_collections().collections
    existing_collection_names = {collection.name for collection in collections}

    if settings.qdrant_collection in existing_collection_names:
        return

    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(
            size=get_embedding_dimension(),
            distance=Distance.COSINE,
        ),
    )


def upsert_chunks_to_qdrant(points: list[PointStruct]) -> None:
    client = get_qdrant_client()

    client.upsert(
        collection_name=settings.qdrant_collection,
        points=points,
    )


def delete_points_from_qdrant(point_ids: list[str]) -> None:
    if not point_ids:
        return

    client = get_qdrant_client()

    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=PointIdsList(points=point_ids),
    )


def build_metadata_filter(
    document_type: str | None = None,
    policy_name: str | None = None,
    department_owner: str | None = None,
    access_level: str | None = None,
    chunk_type: str | None = None,
) -> Filter | None:
    conditions = []

    if document_type:
        conditions.append(
            FieldCondition(
                key="document_type",
                match=MatchValue(value=document_type),
            )
        )

    if policy_name:
        conditions.append(
            FieldCondition(
                key="policy_name",
                match=MatchValue(value=policy_name),
            )
        )

    if department_owner:
        conditions.append(
            FieldCondition(
                key="department_owner",
                match=MatchValue(value=department_owner),
            )
        )

    if access_level:
        conditions.append(
            FieldCondition(
                key="access_level",
                match=MatchValue(value=access_level),
            )
        )

    if chunk_type:
        conditions.append(
            FieldCondition(
                key="chunk_type",
                match=MatchValue(value=chunk_type),
            )
        )

    if not conditions:
        return None

    return Filter(must=conditions)


def search_relevant_chunks(
    query: str,
    top_k: int = 5,
    score_threshold: float | None = None,
    document_type: str | None = None,
    policy_name: str | None = None,
    department_owner: str | None = None,
    access_level: str | None = None,
    chunk_type: str | None = None,
) -> list[dict[str, Any]]:
    ensure_qdrant_collection()

    client = get_qdrant_client()
    query_vector = embed_text(query)

    query_filter = build_metadata_filter(
        document_type=document_type,
        policy_name=policy_name,
        department_owner=department_owner,
        access_level=access_level,
        chunk_type=chunk_type,
    )

    search_results = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True,
        score_threshold=score_threshold,
    )

    results: list[dict[str, Any]] = []

    for result in search_results:
        payload = result.payload or {}

        results.append(
            {
                "score": result.score,
                "text": payload.get("text"),
                "source": {
                    "document_id": payload.get("document_id"),
                    "file_name": payload.get("file_name"),
                    "document_type": payload.get("document_type"),
                    "policy_name": payload.get("policy_name"),
                    "department_owner": payload.get("department_owner"),
                    "access_level": payload.get("access_level"),
                    "page_number": payload.get("page_number"),
                    "chunk_index": payload.get("chunk_index"),
                    "section_title": payload.get("section_title"),
                    "chunk_type": payload.get("chunk_type"),
                    "extractor": payload.get("extractor"),
                    "ocr_applied": payload.get("ocr_applied"),
                },
            }
        )

    return results