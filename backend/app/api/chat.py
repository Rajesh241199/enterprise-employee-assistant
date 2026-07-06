from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.access_control import resolve_rag_access_levels
from app.core.permissions import require_authenticated_user
from app.db.models import User
from app.db.session import get_db
from app.rag.answer_generation import (
    build_rag_prompt,
    calculate_confidence,
    generate_answer_with_ollama,
    select_best_sources,
)
from app.rag.query_rewrite import rewrite_query_with_ollama
from app.rag.reranking import rerank_chunks
from app.rag.retrieval import search_relevant_chunks
from app.schemas.chat import (
    AnswerSource,
    AskRequest,
    AskResponse,
    RetrieveRequest,
    RetrieveResponse,
)
from app.services.event_service import answer_event_question
from app.services.poc_lookup import answer_poc_question
from app.services.policy_service import answer_holiday_question
from app.services.query_router import ChatRoute, classify_chat_route
from app.services.tax_calculator import answer_tax_question


router = APIRouter()


LEAVE_TYPE_KEYWORDS = {
    "privilege_leave": {
        "positive": [
            "privilege leave",
            "leave: privilege leave",
            "pl ",
            " pl",
        ],
        "negative": [
            "paternity leave",
            "maternity leave",
            "sick leave",
            "casual leave",
            "loss of pay",
            "lop",
        ],
    },
    "sick_leave": {
        "positive": [
            "sick leave",
            "leave: sick leave",
            "sl ",
            " sl",
        ],
        "negative": [
            "privilege leave",
            "paternity leave",
            "maternity leave",
            "casual leave",
        ],
    },
    "casual_leave": {
        "positive": [
            "casual leave",
            "leave: casual leave",
            "cl ",
            " cl",
        ],
        "negative": [
            "privilege leave",
            "paternity leave",
            "maternity leave",
            "sick leave",
        ],
    },
    "paternity_leave": {
        "positive": [
            "paternity leave",
        ],
        "negative": [
            "maternity leave",
            "sick leave",
            "casual leave",
        ],
    },
    "maternity_leave": {
        "positive": [
            "maternity leave",
        ],
        "negative": [
            "paternity leave",
            "sick leave",
            "casual leave",
        ],
    },
}


def build_filter_response(
    payload: RetrieveRequest | AskRequest,
    enforced_access_levels: list[str] | None = None,
) -> dict:
    return {
        "document_type": payload.document_type,
        "policy_name": payload.policy_name,
        "department_owner": payload.department_owner,
        "requested_access_level": payload.access_level,
        "enforced_access_levels": enforced_access_levels,
        "chunk_type": payload.chunk_type,
    }


def get_retrieval_query(payload: RetrieveRequest | AskRequest) -> str:
    if not payload.use_query_rewriting:
        return payload.query

    return rewrite_query_with_ollama(payload.query)


def detect_leave_focus(query: str, rewritten_query: str) -> str | None:
    combined_query = f"{query} {rewritten_query}".lower()
    padded_query = f" {combined_query} "

    if "privilege leave" in combined_query or " pl " in padded_query:
        return "privilege_leave"

    if "sick leave" in combined_query or " sl " in padded_query:
        return "sick_leave"

    if "casual leave" in combined_query or " cl " in padded_query:
        return "casual_leave"

    if "paternity leave" in combined_query:
        return "paternity_leave"

    if "maternity leave" in combined_query:
        return "maternity_leave"

    return None


def chunk_matches_leave_focus(chunk_text: str, focus: str) -> bool:
    rules = LEAVE_TYPE_KEYWORDS.get(focus)

    if not rules:
        return True

    normalized_text = f" {chunk_text.lower()} "

    has_positive_signal = any(
        keyword in normalized_text
        for keyword in rules["positive"]
    )

    if not has_positive_signal:
        return False

    early_text = normalized_text[:350]

    has_negative_signal_early = any(
        keyword in early_text
        for keyword in rules["negative"]
    )

    if has_negative_signal_early:
        return False

    return True


def apply_domain_specific_filtering(
    query: str,
    rewritten_query: str,
    chunks: list[dict],
) -> list[dict]:
    focus = detect_leave_focus(
        query=query,
        rewritten_query=rewritten_query,
    )

    if not focus:
        return chunks

    filtered_chunks = []

    for chunk in chunks:
        chunk_text = chunk.get("text") or ""

        if chunk_matches_leave_focus(
            chunk_text=chunk_text,
            focus=focus,
        ):
            filtered_chunks.append(chunk)

    if not filtered_chunks:
        return chunks

    return filtered_chunks


def filter_low_quality_reranked_chunks(
    chunks: list[dict],
    min_rerank_score: float = 0.65,
) -> list[dict]:
    if not chunks:
        return []

    chunks_with_rerank_score = [
        chunk for chunk in chunks
        if chunk.get("rerank_score") is not None
    ]

    if not chunks_with_rerank_score:
        return chunks

    high_quality_chunks = [
        chunk for chunk in chunks
        if (chunk.get("rerank_score") or 0.0) >= min_rerank_score
    ]

    if not high_quality_chunks:
        return chunks

    return high_quality_chunks


def deduplicate_chunks(chunks: list[dict]) -> list[dict]:
    unique_chunks: list[dict] = []
    seen_keys: set[tuple] = set()

    for chunk in chunks:
        source = chunk.get("source", {})

        key = (
            source.get("document_id"),
            source.get("page_number"),
            source.get("chunk_index"),
        )

        if key in seen_keys:
            continue

        seen_keys.add(key)
        unique_chunks.append(chunk)

    return unique_chunks


def search_relevant_chunks_with_access_control(
    payload: RetrieveRequest | AskRequest,
    retrieval_query: str,
    top_k: int,
    enforced_access_levels: list[str],
) -> list[dict]:
    """
    Secure retrieval.

    The request body no longer decides document access.
    The backend searches only across access levels allowed for the logged-in user.
    """

    combined_results: list[dict] = []

    for access_level in enforced_access_levels:
        access_level_results = search_relevant_chunks(
            query=retrieval_query,
            top_k=top_k,
            score_threshold=payload.score_threshold,
            document_type=payload.document_type,
            policy_name=payload.policy_name,
            department_owner=payload.department_owner,
            access_level=access_level,
            chunk_type=payload.chunk_type,
        )

        combined_results.extend(access_level_results)

    unique_results = deduplicate_chunks(combined_results)

    unique_results.sort(
        key=lambda chunk: chunk.get("score") or 0.0,
        reverse=True,
    )

    return unique_results[:top_k]


def retrieve_and_optionally_rerank(
    payload: RetrieveRequest | AskRequest,
    retrieval_query: str,
    current_user: User,
) -> tuple[list[dict], list[str]]:
    enforced_access_levels = resolve_rag_access_levels(
        user=current_user,
        requested_access_level=payload.access_level,
    )

    dense_candidate_limit = (
        payload.candidate_k
        if payload.use_reranking
        else payload.top_k
    )

    dense_results = search_relevant_chunks_with_access_control(
        payload=payload,
        retrieval_query=retrieval_query,
        top_k=dense_candidate_limit,
        enforced_access_levels=enforced_access_levels,
    )

    if not dense_results:
        return [], enforced_access_levels

    precision_filtered_results = apply_domain_specific_filtering(
        query=payload.query,
        rewritten_query=retrieval_query,
        chunks=dense_results,
    )

    if not payload.use_reranking:
        return precision_filtered_results[: payload.top_k], enforced_access_levels

    reranked_results = rerank_chunks(
        query=retrieval_query,
        chunks=precision_filtered_results,
        top_n=payload.top_k,
    )

    quality_filtered_results = filter_low_quality_reranked_chunks(
        chunks=reranked_results,
        min_rerank_score=0.65,
    )

    return quality_filtered_results[: payload.top_k], enforced_access_levels


def build_rag_sources(selected_chunks: list[dict]) -> list[AnswerSource]:
    sources: list[AnswerSource] = []

    for index, chunk in enumerate(selected_chunks, start=1):
        source = chunk.get("source", {})
        text = chunk.get("text") or ""

        sources.append(
            AnswerSource(
                source_id=index,
                score=chunk.get("score"),
                rerank_score=chunk.get("rerank_score"),
                document_id=source.get("document_id"),
                file_name=source.get("file_name"),
                policy_name=source.get("policy_name"),
                document_type=source.get("document_type"),
                department_owner=source.get("department_owner"),
                page_number=source.get("page_number"),
                chunk_index=source.get("chunk_index"),
                chunk_type=source.get("chunk_type"),
                text_preview=text[:300],
            )
        )

    return sources


def handle_structured_route(
    route: ChatRoute,
    payload: AskRequest,
    db: Session,
    current_user: User,
) -> AskResponse | None:
    if route == ChatRoute.HOLIDAYS:
        answer, results_count = answer_holiday_question(
            db=db,
            query=payload.query,
        )

        return AskResponse(
            query=payload.query,
            rewritten_query=None,
            route=route.value,
            answer=answer,
            confidence="high" if results_count else "low",
            use_reranking=False,
            use_query_rewriting=False,
            filters=build_filter_response(payload),
            results_count=results_count,
            sources=[],
        )

    if route == ChatRoute.EVENTS:
        answer, results_count = answer_event_question(
            db=db,
            query=payload.query,
        )

        return AskResponse(
            query=payload.query,
            rewritten_query=None,
            route=route.value,
            answer=answer,
            confidence="high" if results_count else "low",
            use_reranking=False,
            use_query_rewriting=False,
            filters=build_filter_response(payload),
            results_count=results_count,
            sources=[],
        )

    if route == ChatRoute.POC:
        answer, results_count = answer_poc_question(
            db=db,
            query=payload.query,
            current_user=current_user,
        )

        return AskResponse(
            query=payload.query,
            rewritten_query=None,
            route=route.value,
            answer=answer,
            confidence="high" if results_count else "low",
            use_reranking=False,
            use_query_rewriting=False,
            filters=build_filter_response(payload),
            results_count=results_count,
            sources=[],
        )

    if route == ChatRoute.TAX:
        answer = answer_tax_question()

        return AskResponse(
            query=payload.query,
            rewritten_query=None,
            route=route.value,
            answer=answer,
            confidence="medium",
            use_reranking=False,
            use_query_rewriting=False,
            filters=build_filter_response(payload),
            results_count=0,
            sources=[],
        )

    return None


@router.post("/chat/retrieve", response_model=RetrieveResponse)
def retrieve_relevant_chunks(
    payload: RetrieveRequest,
    current_user: User = Depends(require_authenticated_user),
):
    retrieval_query = get_retrieval_query(payload)

    results, enforced_access_levels = retrieve_and_optionally_rerank(
        payload=payload,
        retrieval_query=retrieval_query,
        current_user=current_user,
    )

    return RetrieveResponse(
        query=payload.query,
        rewritten_query=retrieval_query,
        top_k=payload.top_k,
        candidate_k=payload.candidate_k,
        score_threshold=payload.score_threshold,
        use_reranking=payload.use_reranking,
        use_query_rewriting=payload.use_query_rewriting,
        filters=build_filter_response(
            payload=payload,
            enforced_access_levels=enforced_access_levels,
        ),
        results_count=len(results),
        results=results,
    )


@router.post("/chat/ask", response_model=AskResponse)
def ask_question(
    payload: AskRequest,
    current_user: User = Depends(require_authenticated_user),
    db: Session = Depends(get_db),
):
    route = classify_chat_route(payload.query)

    structured_response = handle_structured_route(
        route=route,
        payload=payload,
        db=db,
        current_user=current_user,
    )

    if structured_response:
        return structured_response

    retrieval_query = get_retrieval_query(payload)

    retrieved_chunks, enforced_access_levels = retrieve_and_optionally_rerank(
        payload=payload,
        retrieval_query=retrieval_query,
        current_user=current_user,
    )

    if not retrieved_chunks:
        return AskResponse(
            query=payload.query,
            rewritten_query=retrieval_query,
            route=ChatRoute.POLICY_RAG.value,
            answer="I could not find this information in the available company documents.",
            confidence="low",
            use_reranking=payload.use_reranking,
            use_query_rewriting=payload.use_query_rewriting,
            filters=build_filter_response(
                payload=payload,
                enforced_access_levels=enforced_access_levels,
            ),
            results_count=0,
            sources=[],
        )

    selected_chunks = select_best_sources(
        retrieved_chunks=retrieved_chunks,
        max_sources=payload.max_sources,
    )

    confidence = calculate_confidence(selected_chunks)

    prompt = build_rag_prompt(
        question=payload.query,
        retrieved_chunks=selected_chunks,
    )

    try:
        answer = generate_answer_with_ollama(prompt)

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer with Ollama: {str(exc)}",
        ) from exc

    sources = build_rag_sources(selected_chunks)

    return AskResponse(
        query=payload.query,
        rewritten_query=retrieval_query,
        route=ChatRoute.POLICY_RAG.value,
        answer=answer,
        confidence=confidence,
        use_reranking=payload.use_reranking,
        use_query_rewriting=payload.use_query_rewriting,
        filters=build_filter_response(
            payload=payload,
            enforced_access_levels=enforced_access_levels,
        ),
        results_count=len(selected_chunks),
        sources=sources,
    )