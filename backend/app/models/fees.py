import uuid
from typing import Optional, List
from datetime import date, datetime, timezone
import enum
from sqlalchemy import String, Boolean, Date, DateTime, Integer, Numeric, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class FeeStatus(str, enum.Enum):
    UNPAID = "UNPAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    WAIVED = "WAIVED"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, enum.Enum):
    BANK_TRANSFER = "BANK_TRANSFER"
    CASH = "CASH"
    M_PESA = "M_PESA"
    AIRTEL_MONEY = "AIRTEL_MONEY"
    TIGO_PESA = "TIGO_PESA"
    HALOPESA = "HALOPESA"


class FeeCategory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fee_categories"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "Tuition", "Transport", "Meals", "Uniforms", "Examination"
    code: Mapped[str] = mapped_column(String(50), nullable=False)   # "TUITION", "TRANSPORT"
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_school_fee_category_code"),
    )


class FeeStructure(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fee_structures"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_term_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_terms.id", ondelete="SET NULL"), nullable=True, index=True)
    fee_category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    amount_tzs: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    category: Mapped["FeeCategory"] = relationship("FeeCategory")
    assignments: Mapped[List["FeeAssignment"]] = relationship("FeeAssignment", back_populates="fee_structure", cascade="all, delete-orphan")


class FeeAssignment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fee_assignments"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    fee_structure_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_structures.id", ondelete="CASCADE"), nullable=False, index=True)
    class_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=True, index=True)
    student_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)
    amount_tzs: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    fee_structure: Mapped["FeeStructure"] = relationship("FeeStructure", back_populates="assignments")


class StudentFeeAccount(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "student_fee_accounts"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    total_invoiced_tzs: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)
    total_paid_tzs: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)
    total_waived_tzs: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)
    outstanding_balance_tzs: Mapped[float] = mapped_column(Numeric(14, 2), default=0.0, nullable=False)

    student: Mapped["Student"] = relationship("Student")

    __table_args__ = (
        UniqueConstraint("student_id", "academic_year_id", name="uq_student_year_fee_account"),
    )


class FeeInvoice(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fee_invoices"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_term_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_terms.id", ondelete="SET NULL"), nullable=True)
    invoice_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    total_amount_tzs: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    balance_due_tzs: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[FeeStatus] = mapped_column(SQLEnum(FeeStatus), default=FeeStatus.UNPAID, nullable=False, index=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    items: Mapped[List["FeeInvoiceItem"]] = relationship("FeeInvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments: Mapped[List["FeePayment"]] = relationship("FeePayment", back_populates="invoice")
    student: Mapped["Student"] = relationship("Student")


class FeeInvoiceItem(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fee_invoice_items"

    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    fee_category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_categories.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount_tzs: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    invoice: Mapped["FeeInvoice"] = relationship("FeeInvoice", back_populates="items")


class FeePayment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fee_payments"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_invoices.id", ondelete="SET NULL"), nullable=True, index=True)
    receipt_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount_tzs: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(SQLEnum(PaymentMethod), default=PaymentMethod.BANK_TRANSFER, nullable=False)
    transaction_reference: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    recorded_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    invoice: Mapped[Optional["FeeInvoice"]] = relationship("FeeInvoice", back_populates="payments")
    allocations: Mapped[List["FeePaymentAllocation"]] = relationship("FeePaymentAllocation", back_populates="payment", cascade="all, delete-orphan")


class FeePaymentAllocation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fee_payment_allocations"

    payment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_payments.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_invoice_items.id", ondelete="CASCADE"), nullable=False, index=True)
    allocated_amount_tzs: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    payment: Mapped["FeePayment"] = relationship("FeePayment", back_populates="allocations")


class FeeAdjustment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fee_adjustments"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    adjustment_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "DISCOUNT", "WAIVER", "CORRECTION"
    amount_tzs: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    authorized_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


class FeeReminderRule(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fee_reminder_rules"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    days_relative_to_due_date: Mapped[int] = mapped_column(Integer, nullable=False)  # e.g., -14, -7, -3, 0, 7, 14
    reminder_channel: Mapped[str] = mapped_column(String(50), default="SMS", nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("message_templates.id", ondelete="SET NULL"), nullable=True)


class FeeReminderJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fee_reminder_jobs"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    reminder_rule_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_reminder_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_for: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)  # PENDING, PROCESSED, CANCELLED, FAILED


class FeeReminderHistory(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "fee_reminder_history"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("fee_reminder_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    guardian_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guardians.id", ondelete="CASCADE"), nullable=False, index=True)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    amount_outstanding_tzs: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    campaign_recipient_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("campaign_recipients.id", ondelete="SET NULL"), nullable=True)
