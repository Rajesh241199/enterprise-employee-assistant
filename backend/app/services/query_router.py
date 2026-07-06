from enum import Enum


class ChatRoute(str, Enum):
    POLICY_RAG = "policy_rag"
    HOLIDAYS = "holidays"
    EVENTS = "events"
    POC = "poc"
    TAX = "tax"


def classify_chat_route(query: str) -> ChatRoute:
    normalized_query = query.lower().strip()

    holiday_keywords = [
        "holiday",
        "holidays",
        "public holiday",
        "company holiday",
        "next holiday",
        "diwali",
        "independence day",
        "republic day",
    ]

    event_keywords = [
        "event",
        "events",
        "workshop",
        "training",
        "townhall",
        "town hall",
        "session",
        "upcoming event",
        "company event",
    ]

    poc_keywords = [
        "poc",
        "point of contact",
        "contact person",
        "who should i contact",
        "whom should i contact",
        "hr contact",
        "finance contact",
        "it contact",
        "data science contact",
    ]

    tax_keywords = [
        "tax",
        "tax regime",
        "old regime",
        "new regime",
        "income tax",
        "80c",
        "hra",
        "deduction",
        "salary tax",
    ]

    if any(keyword in normalized_query for keyword in holiday_keywords):
        return ChatRoute.HOLIDAYS

    if any(keyword in normalized_query for keyword in event_keywords):
        return ChatRoute.EVENTS

    if any(keyword in normalized_query for keyword in poc_keywords):
        return ChatRoute.POC

    if any(keyword in normalized_query for keyword in tax_keywords):
        return ChatRoute.TAX

    return ChatRoute.POLICY_RAG