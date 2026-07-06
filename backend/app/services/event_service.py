from sqlalchemy import text
from sqlalchemy.orm import Session


def is_next_event_query(query: str) -> bool:
    normalized_query = query.lower()

    next_keywords = [
        "next event",
        "nearest event",
        "coming event",
        "upcoming event",
        "next company event",
        "when is the next",
    ]

    return any(keyword in normalized_query for keyword in next_keywords)


def get_upcoming_events(db: Session, limit: int = 5) -> list[dict]:
    query = text(
        """
        SELECT
            id,
            event_name,
            description,
            event_date,
            start_time,
            end_time,
            location,
            organizer,
            preparation_notes
        FROM events
        WHERE event_date >= CURRENT_DATE
        ORDER BY event_date ASC, start_time ASC
        LIMIT :limit
        """
    )

    rows = db.execute(query, {"limit": limit}).mappings().all()

    return [dict(row) for row in rows]


def format_next_event_answer(events: list[dict]) -> str:
    if not events:
        return "I could not find any upcoming company event."

    event = events[0]

    lines = [
        "The next company event is:",
        f"- {event.get('event_name')}",
        f"  Date: {event.get('event_date')}",
        f"  Time: {event.get('start_time')} - {event.get('end_time')}",
        f"  Location: {event.get('location')}",
        f"  Organizer: {event.get('organizer')}",
    ]

    if event.get("preparation_notes"):
        lines.append(f"  Preparation: {event.get('preparation_notes')}")

    return "\n".join(lines)


def format_events_answer(events: list[dict]) -> str:
    if not events:
        return "I could not find any upcoming company events."

    lines = ["Here are the upcoming company events:"]

    for event in events:
        lines.append(
            "\n"
            f"- {event.get('event_name')}\n"
            f"  Date: {event.get('event_date')}\n"
            f"  Time: {event.get('start_time')} - {event.get('end_time')}\n"
            f"  Location: {event.get('location')}\n"
            f"  Organizer: {event.get('organizer')}"
        )

        if event.get("preparation_notes"):
            lines.append(f"  Preparation: {event.get('preparation_notes')}")

    return "\n".join(lines)


def answer_event_question(db: Session, query: str) -> tuple[str, int]:
    if is_next_event_query(query):
        events = get_upcoming_events(db=db, limit=1)
        return format_next_event_answer(events), len(events)

    events = get_upcoming_events(db=db, limit=5)
    return format_events_answer(events), len(events)