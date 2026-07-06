import re

import httpx

from app.core.config import settings


def clean_llm_answer(answer: str) -> str:
    answer = answer.strip()

    # Convert escaped newlines into real line breaks
    answer = answer.replace("\\n", "\n")

    # Reduce too many blank lines
    answer = re.sub(r"\n{3,}", "\n\n", answer)

    return answer.strip()


def calculate_confidence(retrieved_chunks: list[dict]) -> str:
    if not retrieved_chunks:
        return "low"

    top_chunk = retrieved_chunks[0]

    top_score = (
        top_chunk.get("rerank_score")
        if top_chunk.get("rerank_score") is not None
        else top_chunk.get("score", 0.0)
    )

    top_score = top_score or 0.0

    if top_score >= 0.70:
        return "high"

    if top_score >= 0.50:
        return "medium"

    return "low"


def select_best_sources(
    retrieved_chunks: list[dict],
    max_sources: int = 3,
) -> list[dict]:
    selected_sources: list[dict] = []
    seen_keys: set[tuple] = set()

    for chunk in retrieved_chunks:
        source = chunk.get("source", {})

        key = (
            source.get("document_id"),
            source.get("page_number"),
            source.get("chunk_index"),
        )

        if key in seen_keys:
            continue

        seen_keys.add(key)
        selected_sources.append(chunk)

        if len(selected_sources) >= max_sources:
            break

    return selected_sources


def build_rag_prompt(question: str, retrieved_chunks: list[dict]) -> str:
    context_blocks = []

    for index, chunk in enumerate(retrieved_chunks, start=1):
        source = chunk.get("source", {})

        context_blocks.append(
            f"""
[Source {index}]
File: {source.get("file_name")}
Policy: {source.get("policy_name")}
Page: {source.get("page_number")}
Chunk Index: {source.get("chunk_index")}
Chunk Type: {source.get("chunk_type")}
Dense Score: {chunk.get("score")}
Rerank Score: {chunk.get("rerank_score")}

Content:
{chunk.get("text")}
""".strip()
        )

    context_text = "\n\n---\n\n".join(context_blocks)

    return f"""
You are an internal employee policy assistant.

Your task:
Answer the employee question using ONLY the retrieved company policy context.

Strict rules:
1. Do not use outside knowledge.
2. Do not invent policy rules, numbers, dates, benefits, or approval steps.
3. Answer only what the employee asked.
4. Do not include related policy rules unless they directly answer the question.
5. If the answer is not available in the context, say:
   "I could not find this information in the available company documents."
6. Keep the answer concise and employee-friendly.
7. Prefer 2 to 5 short bullet points only when the answer has multiple rules.
8. Always cite the relevant source using [Source 1], [Source 2], etc.
9. Do not copy the full raw context. Summarize only the answer.

Employee question:
{question}

Retrieved company context:
{context_text}

Final answer:
""".strip()


def generate_answer_with_ollama(prompt: str) -> str:
    url = f"{settings.ollama_base_url}/api/generate"

    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_ctx": 4096,
        },
    }

    response = httpx.post(url, json=payload, timeout=120)
    response.raise_for_status()

    data = response.json()
    raw_answer = data.get("response", "").strip()

    return clean_llm_answer(raw_answer)