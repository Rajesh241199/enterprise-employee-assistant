from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.permissions import require_authenticated_user
from app.db.models import Event, Holiday, User
from app.db.session import get_db


router = APIRouter()


@router.get("/holidays")
def get_holidays(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user),
):
    holidays = db.query(Holiday).order_by(Holiday.holiday_date.asc()).all()

    return [
        {
            "id": holiday.id,
            "holiday_name": holiday.holiday_name,
            "holiday_date": holiday.holiday_date.isoformat(),
            "location": holiday.location,
            "holiday_type": holiday.holiday_type,
        }
        for holiday in holidays
    ]


@router.get("/events/upcoming")
def get_upcoming_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user),
):
    events = (
        db.query(Event)
        .filter(Event.event_date >= date.today())
        .order_by(Event.event_date.asc())
        .all()
    )

    return [
        {
            "id": event.id,
            "event_name": event.event_name,
            "description": event.description,
            "event_date": event.event_date.isoformat(),
            "start_time": event.start_time,
            "end_time": event.end_time,
            "location": event.location,
            "organizer": event.organizer,
            "preparation_notes": event.preparation_notes,
            "event_metadata": event.event_metadata,
        }
        for event in events
    ]