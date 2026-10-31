import uuid
from typing import Optional, List
from datetime import date, time, datetime, timezone
import enum
from sqlalchemy import String, Boolean, Date, Time, DateTime, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class MeetingResponseStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    TENTATIVE = "TENTATIVE"


class SchoolMeeting(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "school_meetings"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meeting_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    venue: Mapped[str] = mapped_column(String(255), nullable=False)

    invitations: Mapped[List["MeetingInvitation"]] = relationship("MeetingInvitation", back_populates="meeting", cascade="all, delete-orphan")


class MeetingInvitation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "meeting_invitations"

    meeting_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("school_meetings.id", ondelete="CASCADE"), nullable=False, index=True)
    class_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="SET NULL"), nullable=True, index=True)
    student_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    guardian_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guardians.id", ondelete="CASCADE"), nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    invitation_status: Mapped[str] = mapped_column(String(50), default="SENT", nullable=False)

    meeting: Mapped["SchoolMeeting"] = relationship("SchoolMeeting", back_populates="invitations")
    guardian: Mapped["Guardian"] = relationship("Guardian")
    responses: Mapped[List["MeetingResponse"]] = relationship("MeetingResponse", back_populates="invitation", cascade="all, delete-orphan")


class MeetingResponse(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "meeting_responses"

    invitation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("meeting_invitations.id", ondelete="CASCADE"), nullable=False, index=True)
    guardian_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guardians.id", ondelete="CASCADE"), nullable=False, index=True)
    response_status: Mapped[MeetingResponseStatus] = mapped_column(SQLEnum(MeetingResponseStatus), default=MeetingResponseStatus.CONFIRMED, nullable=False)
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    channel: Mapped[str] = mapped_column(String(50), default="SMS", nullable=False)  # SMS, USSD, PORTAL
    responded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    invitation: Mapped["MeetingInvitation"] = relationship("MeetingInvitation", back_populates="responses")
