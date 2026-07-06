from sqlalchemy import text
from sqlalchemy.orm import Session


def is_next_holiday_query(query: str) -> bool:
    normalized_query = query.lower()

    next_keywords = [
        "next holiday",
        "nearest holiday",
        "coming holiday",
        "upcoming holiday",
        "when is the next",
    ]

    return any(keyword in normalized_query for keyword in next_keywords)


def get_upcoming_holidays(db: Session, limit: int = 5) -> list[dict]:
    query = text(
        """
        SELECT
            id,
            holiday_name,
            holiday_date,
            location,
            holiday_type
        FROM holidays
        WHERE holiday_date >= CURRENT_DATE
        ORDER BY holiday_date ASC
        LIMIT :limit
        """
    )

    rows = db.execute(query, {"limit": limit}).mappings().all()

    return [dict(row) for row in rows]


def format_next_holiday_answer(holidays: list[dict]) -> str:
    if not holidays:
        return "I could not find any upcoming holiday in the company holiday records."

    holiday = holidays[0]

    return (
        "The next company holiday is:\n"
        f"- {holiday.get('holiday_name')} — {holiday.get('holiday_date')} "
        f"({holiday.get('location')}, {holiday.get('holiday_type')})"
    )


def format_holidays_answer(holidays: list[dict]) -> str:
    if not holidays:
        return "I could not find any upcoming holidays in the company holiday records."

    lines = ["Here are the upcoming holidays:"]

    for holiday in holidays:
        lines.append(
            "- "
            f"{holiday.get('holiday_name')} — "
            f"{holiday.get('holiday_date')} "
            f"({holiday.get('location')}, {holiday.get('holiday_type')})"
        )

    return "\n".join(lines)


def answer_holiday_question(db: Session, query: str) -> tuple[str, int]:
    if is_next_holiday_query(query):
        holidays = get_upcoming_holidays(db=db, limit=1)
        return format_next_holiday_answer(holidays), len(holidays)

    holidays = get_upcoming_holidays(db=db, limit=5)
    return format_holidays_answer(holidays), len(holidays)