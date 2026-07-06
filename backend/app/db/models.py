from datetime import date, datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, Enum):
    EMPLOYEE = "employee"
    HR_ADMIN = "hr_admin"
    FINANCE_ADMIN = "finance_admin"
    IT_ADMIN = "it_admin"
    SUPER_ADMIN = "super_admin"


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    INDEXED = "indexed"
    FAILED = "failed"


class FeedbackRating(str, Enum):
    GOOD = "good"
    BAD = "bad"


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    users: Mapped[list["User"]] = relationship(
        back_populates="department",
        cascade="all, delete-orphan",
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    employee_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[str] = mapped_column(String(50), default=UserRole.EMPLOYEE.value)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(150), nullable=True)

    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    department: Mapped["Department | None"] = relationship(back_populates="users")
    uploaded_documents: Mapped[list["Document"]] = relationship(back_populates="uploaded_by_user")
    chat_sessions: Mapped[list["ChatSession"]] = relationship(back_populates="user")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    document_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    policy_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    department_owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    access_level: Mapped[str] = mapped_column(String(100), default="all_employees")

    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_updated: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(String(50), default=DocumentStatus.UPLOADED.value)

    uploaded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    extra_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    uploaded_by_user: Mapped["User | None"] = relationship(back_populates="uploaded_documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
    )

    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    qdrant_point_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    chunk_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    document: Mapped["Document"] = relationship(back_populates="chunks")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    event_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[str | None] = mapped_column(String(20), nullable=True)
    end_time: Mapped[str | None] = mapped_column(String(20), nullable=True)

    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organizer: Mapped[str | None] = mapped_column(String(150), nullable=True)

    preparation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Holiday(Base):
    __tablename__ = "holidays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    holiday_name: Mapped[str] = mapped_column(String(255), nullable=False)
    holiday_date: Mapped[date] = mapped_column(Date, nullable=False)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    holiday_type: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class EmployeePOCMapping(Base):
    __tablename__ = "employee_poc_mapping"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    department: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)

    hr_poc_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    hr_poc_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    it_poc_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    it_poc_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    buddy_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    buddy_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class TaxSlab(Base):
    __tablename__ = "tax_slabs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    financial_year: Mapped[str] = mapped_column(String(20), nullable=False)
    regime: Mapped[str] = mapped_column(String(50), nullable=False)

    min_income: Mapped[float] = mapped_column(Float, nullable=False)
    max_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    tax_rate: Mapped[float] = mapped_column(Float, nullable=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="chat_sessions")
    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id"),
        nullable=False,
        index=True,
    )

    user_question: Mapped[str] = mapped_column(Text, nullable=False)
    rewritten_question: Mapped[str | None] = mapped_column(Text, nullable=True)

    assistant_answer: Mapped[str] = mapped_column(Text, nullable=False)

    retrieved_sources: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(50), nullable=True)

    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["ChatSession"] = relationship(back_populates="messages")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    chat_message_id: Mapped[int | None] = mapped_column(
        ForeignKey("chat_messages.id"),
        nullable=True,
    )

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    rating: Mapped[str] = mapped_column(String(50), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )