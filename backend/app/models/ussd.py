import uuid
from typing import Optional, List, Any
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Integer, Text, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class UssdSession(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ussd_sessions"

    session_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    service_code: Mapped[str] = mapped_column(String(50), default="*384*55#", nullable=False)
    current_menu: Mapped[str] = mapped_column(String(100), default="MAIN_MENU", nullable=False)
    session_data: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    events: Mapped[List["UssdSessionEvent"]] = relationship("UssdSessionEvent", back_populates="session", cascade="all, delete-orphan")


class UssdSessionEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ussd_session_events"

    ussd_session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ussd_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    user_input: Mapped[str] = mapped_column(String(255), nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_end_step: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    session: Mapped["UssdSession"] = relationship("UssdSession", back_populates="events")


class UssdAccessAudit(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "ussd_access_audits"

    phone_number: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    guardian_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("guardians.id", ondelete="SET NULL"), nullable=True)
    action_attempted: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # SUCCESS, UNAUTHORIZED, FAILED
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
