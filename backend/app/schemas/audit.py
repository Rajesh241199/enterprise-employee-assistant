from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditActor(BaseModel):
    user_id: int | None = None
    email: str | None = None
    role: str | None = None


class AuditClient(BaseModel):
    ip: str | None = None
    user_agent: str | None = None


class AuditResource(BaseModel):
    type: str | None = None
    id: str | None = None


class AuditLogItem(BaseModel):
    id: int
    timestamp: datetime
    event_type: str
    outcome: str
    request_id: str | None = None

    actor: AuditActor
    client: AuditClient
    resource: AuditResource

    metadata: dict[str, Any]


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItem]

    total: int
    offset: int
    limit: int


class AuditLogSummaryResponse(BaseModel):
    total_events: int
    successful_events: int
    failed_events: int
    blocked_events: int
    events_last_24_hours: int