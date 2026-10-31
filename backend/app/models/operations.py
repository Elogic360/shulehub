import uuid
from typing import Optional, List, Any
from datetime import date, datetime, timezone
import enum
from sqlalchemy import String, Boolean, Date, DateTime, Integer, Numeric, Text, ForeignKey, Enum as SQLEnum, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class SubscriptionStatus(str, enum.Enum):
    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    CANCELLED = "CANCELLED"


class SubscriptionPlan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "subscription_plans"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    max_students: Mapped[int] = mapped_column(Integer, default=500, nullable=False)
    monthly_sms_quota: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    price_tzs: Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    features: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)


class Subscription(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "subscriptions"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subscription_plans.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    sms_credits_remaining: Mapped[int] = mapped_column(Integer, default=500, nullable=False)

    plan: Mapped["SubscriptionPlan"] = relationship("SubscriptionPlan")


class UsageRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "usage_records"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    metric: Mapped[str] = mapped_column(String(50), nullable=False)  # "SMS_SENT", "ACTIVE_STUDENTS", "API_REQUESTS"
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class AuditLog(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "audit_logs"

    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_name: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    changes: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class IdempotencyKey(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    scope: Mapped[str] = mapped_column(String(100), nullable=False)
    response_body: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class OutboxEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "outbox_events"

    aggregate_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    payload: Mapped[Any] = mapped_column(JSON, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ProviderAccount(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "provider_accounts"

    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True)
    provider_name: Mapped[str] = mapped_column(String(50), default="AFRICAS_TALKING", nullable=False)
    api_username: Mapped[str] = mapped_column(String(100), nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(String(255), nullable=False)
    sender_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
