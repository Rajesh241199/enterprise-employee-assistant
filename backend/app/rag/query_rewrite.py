import re

import httpx

from app.core.config import settings


ABBREVIATION_MAP = {
    r"\bPL\b": "Privilege Leave",
    r"\bP\.L\.\b": "Privilege Leave",
    r"\bCL\b": "Casual Leave",
    r"\bSL\b": "Sick Leave",
    r"\bLTA\b": "Leave Travel Allowance",
    r"\bPOC\b": "Point of Contact",
}


def expand_known_abbreviations(query: str) -> str:
    expanded_query = query

    for pattern, replacement in ABBREVIATION_MAP.items():
        expanded_query = re.sub(
            pattern,
            replacement,
            expanded_query,
            flags=re.IGNORECASE,
        )

    return expanded_query


def clean_rewritten_query(text: str, original_query: str) -> str:
    cleaned = text.strip()
    cleaned = cleaned.replace("\\n", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)

    prefixes = [
        "Rewritten query:",
        "Rewritten Query:",
        "Query:",
        "Search query:",
        "Search Query:",
    ]

    for prefix in prefixes:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()

    cleaned = cleaned.strip('"').strip("'").strip()

    if not cleaned:
        return expand_known_abbreviations(original_query)

    if len(cleaned.split()) > 30:
        return expand_known_abbreviations(original_query)

    cleaned = expand_known_abbreviations(cleaned)

    return cleaned


def build_query_rewrite_prompt(query: str) -> str:
    expanded_query = expand_known_abbreviations(query)

    return f"""
You rewrite employee questions into clear search queries for an internal company policy chatbot.

Rules:
1. Do not answer the question.
2. Do not add facts.
3. Do not use outside knowledge.
4. Keep the rewritten query short and specific.
5. Expand employee abbreviations:
   - PL means Privilege Leave
   - CL means Casual Leave
   - SL means Sick Leave
   - LTA means Leave Travel Allowance
   - POC means Point of Contact
6. Return only the rewritten query. No explanation.

Original employee question:
{query}

Expanded employee question:
{expanded_query}

Rewritten search query:
""".strip()


def rewrite_query_with_ollama(query: str) -> str:
    abbreviation_expanded_query = expand_known_abbreviations(query)

    prompt = build_query_rewrite_prompt(query)

    url = f"{settings.ollama_base_url}/api/generate"

    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "top_p": 0.8,
            "num_ctx": 2048,
        },
    }

    try:
        response = httpx.post(url, json=payload, timeout=60)
        response.raise_for_status()

        data = response.json()
        rewritten = data.get("response", "")

        cleaned_query = clean_rewritten_query(
            text=rewritten,
            original_query=abbreviation_expanded_query,
        )

        return cleaned_query

    except Exception:
        return abbreviation_expanded_query