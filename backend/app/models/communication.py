import uuid
from typing import Optional, List, Any
from datetime import datetime, timezone
import enum
from sqlalchemy import String, Boolean, DateTime, Integer, Numeric, Text, ForeignKey, Enum as SQLEnum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class TargetingMode(str, enum.Enum):
    CLASS_BULK = "CLASS_BULK"
    SELECTED_GUARDIANS = "SELECTED_GUARDIANS"
    INDIVIDUAL = "INDIVIDUAL"


class CampaignStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class MessageDeliveryStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    UNKNOWN = "UNKNOWN"


class Announcement(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "announcements"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default="NORMAL", nullable=False)  # LOW, NORMAL, HIGH, URGENT
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    targets: Mapped[List["AnnouncementTarget"]] = relationship("AnnouncementTarget", back_populates="announcement", cascade="all, delete-orphan")
    approvals: Mapped[List["AnnouncementApproval"]] = relationship("AnnouncementApproval", back_populates="announcement", cascade="all, delete-orphan")


class AnnouncementTarget(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "announcement_targets"

    announcement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "ALL", "CLASS", "LEVEL"
    target_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    announcement: Mapped["Announcement"] = relationship("Announcement", back_populates="targets")


class AnnouncementApproval(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "announcement_approvals"

    announcement_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("announcements.id", ondelete="CASCADE"), nullable=False, index=True)
    approver_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED
    comments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    announcement: Mapped["Announcement"] = relationship("Announcement", back_populates="approvals")


class MessageTemplate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "message_templates"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="GENERAL", nullable=False)  # GENERAL, EXAM, FEES, MEETING
    language: Mapped[str] = mapped_column(String(10), default="sw", nullable=False)  # 'sw' or 'en'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # e.g., ["parent_name", "student_name", "fee_balance"]


class CommunicationCampaign(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "communication_campaigns"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    class_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message_content: Mapped[str] = mapped_column(Text, nullable=False)
    targeting_mode: Mapped[TargetingMode] = mapped_column(SQLEnum(TargetMode := TargetingMode), nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(SQLEnum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False, index=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    recipient_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    delivered_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cost_tzs: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)

    recipients: Mapped[List["CampaignRecipient"]] = relationship("CampaignRecipient", back_populates="campaign", cascade="all, delete-orphan")


class CampaignRecipient(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "campaign_recipients"

    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("communication_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    guardian_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guardians.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    personalized_text: Mapped[str] = mapped_column(Text, nullable=False)
    segments: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[MessageDeliveryStatus] = mapped_column(SQLEnum(MessageDeliveryStatus), default=MessageDeliveryStatus.QUEUED, nullable=False, index=True)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)

    campaign: Mapped["CommunicationCampaign"] = relationship("CommunicationCampaign", back_populates="recipients")
    jobs: Mapped[List["MessageJob"]] = relationship("MessageJob", back_populates="recipient", cascade="all, delete-orphan")


class MessageJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "message_jobs"

    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("communication_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaign_recipients.id", ondelete="CASCADE"), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED", nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    recipient: Mapped["CampaignRecipient"] = relationship("CampaignRecipient", back_populates="jobs")
    attempts: Mapped[List["MessageAttempt"]] = relationship("MessageAttempt", back_populates="job", cascade="all, delete-orphan")


class MessageAttempt(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "message_attempts"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("message_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_name: Mapped[str] = mapped_column(String(50), default="AFRICAS_TALKING", nullable=False)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    status: Mapped[MessageDeliveryStatus] = mapped_column(SQLEnum(MessageDeliveryStatus), default=MessageDeliveryStatus.SUBMITTED, nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    response_payload: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    job: Mapped["MessageJob"] = relationship("MessageJob", back_populates="attempts")
    delivery_events: Mapped[List["MessageDeliveryEvent"]] = relationship("MessageDeliveryEvent", back_populates="attempt", cascade="all, delete-orphan")


class MessageDeliveryEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "message_delivery_events"

    attempt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("message_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_message_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    event_status: Mapped[MessageDeliveryStatus] = mapped_column(SQLEnum(MessageDeliveryStatus), nullable=False)
    network_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    attempt: Mapped["MessageAttempt"] = relationship("MessageAttempt", back_populates="delivery_events")


class ProviderWebhookEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "provider_webhook_events"

    provider_name: Mapped[str] = mapped_column(String(50), default="AFRICAS_TALKING", nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # DELIVERY_REPORT, INCOMING_SMS, USSD
    payload: Mapped[Any] = mapped_column(JSON, nullable=False)
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class MessageCostRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "message_cost_records"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("communication_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaign_recipients.id", ondelete="CASCADE"), nullable=False)
    segments: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    cost_tzs: Mapped[float] = mapped_column(Numeric(10, 2), default=0.0, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="TZS", nullable=False)


class ParentAcknowledgement(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "parent_acknowledgements"

    campaign_recipient_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("campaign_recipients.id", ondelete="CASCADE"), nullable=False, index=True)
    guardian_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guardians.id", ondelete="CASCADE"), nullable=False, index=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    channel: Mapped[str] = mapped_column(String(50), default="SMS", nullable=False)  # SMS, USSD, PORTAL
