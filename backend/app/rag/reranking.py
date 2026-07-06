from functools import lru_cache
from math import exp
from typing import Any

from sentence_transformers import CrossEncoder

from app.core.config import settings


@lru_cache
def get_reranker_model() -> CrossEncoder:
    return CrossEncoder(settings.reranker_model)


def sigmoid(value: float) -> float:
    return 1 / (1 + exp(-value))


def rerank_chunks(
    query: str,
    chunks: list[dict[str, Any]],
    top_n: int,
) -> list[dict[str, Any]]:
    if not chunks:
        return []

    model = get_reranker_model()

    query_chunk_pairs = [
        (query, chunk.get("text") or "")
        for chunk in chunks
    ]

    raw_scores = model.predict(query_chunk_pairs)

    reranked_chunks: list[dict[str, Any]] = []

    for chunk, raw_score in zip(chunks, raw_scores):
        raw_score_float = float(raw_score)

        enriched_chunk = {
            **chunk,
            "rerank_score_raw": raw_score_float,
            "rerank_score": sigmoid(raw_score_float),
        }

        reranked_chunks.append(enriched_chunk)

    reranked_chunks.sort(
        key=lambda item: item.get("rerank_score", 0.0),
        reverse=True,
    )

    return reranked_chunks[:top_n]