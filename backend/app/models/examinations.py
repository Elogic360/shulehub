import uuid
from typing import Optional, List, Any
from datetime import date, datetime, timezone
import enum
from sqlalchemy import String, Boolean, Date, DateTime, Integer, Numeric, Text, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class ExamType(str, enum.Enum):
    MONTHLY_TEST = "MONTHLY_TEST"
    MID_TERM = "MID_TERM"
    TERMINAL = "TERMINAL"
    ANNUAL = "ANNUAL"
    MOCK = "MOCK"
    NATIONAL = "NATIONAL"


class ResultStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"  # Alias for RELEASED
    RELEASED = "RELEASED"
    SUPERSEDED = "SUPERSEDED"
    WITHDRAWN = "WITHDRAWN"
    REJECTED = "REJECTED"


class Subject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "subjects"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Mathematics", "Kiswahili"
    code: Mapped[str] = mapped_column(String(50), nullable=False)   # e.g., "MATH", "KISW"
    school_type: Mapped[str] = mapped_column(String(50), default="PRIMARY", nullable=False)

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_school_subject_code"),
    )


class Examination(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "examinations"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_term_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_terms.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)  # e.g., "Term 1 Mid-Term Examination 2026"
    exam_type: Mapped[ExamType] = mapped_column(SQLEnum(ExamType), default=ExamType.MID_TERM, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    exam_subjects: Mapped[List["ExaminationSubject"]] = relationship("ExaminationSubject", back_populates="examination", cascade="all, delete-orphan")


class ExaminationSubject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "examination_subjects"

    examination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    class_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    max_score: Mapped[float] = mapped_column(Numeric(5, 2), default=100.0, nullable=False)
    pass_mark: Mapped[float] = mapped_column(Numeric(5, 2), default=50.0, nullable=False)

    examination: Mapped["Examination"] = relationship("Examination", back_populates="exam_subjects")
    subject: Mapped["Subject"] = relationship("Subject")
    results: Mapped[List["StudentExamResult"]] = relationship("StudentExamResult", back_populates="exam_subject", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("examination_id", "subject_id", "class_group_id", name="uq_exam_subject_class"),
    )


class StudentExamResult(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "student_exam_results"

    examination_subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examination_subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    grade: Mapped[str] = mapped_column(String(5), nullable=False)  # A, B, C, D, F
    remarks: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[ResultStatus] = mapped_column(SQLEnum(ResultStatus), default=ResultStatus.DRAFT, nullable=False)
    approved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    exam_subject: Mapped["ExaminationSubject"] = relationship("ExaminationSubject", back_populates="results")
    student: Mapped["Student"] = relationship("Student")

    __table_args__ = (
        UniqueConstraint("examination_subject_id", "student_id", name="uq_exam_subject_student"),
    )


class ResultImportBatch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "result_import_batches"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    examination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    class_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)  # PENDING, VALIDATED, COMMITTED, FAILED

    errors: Mapped[List["ResultImportError"]] = relationship("ResultImportError", back_populates="batch", cascade="all, delete-orphan")


class ResultImportError(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "result_import_errors"

    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("result_import_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    admission_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)

    batch: Mapped["ResultImportBatch"] = relationship("ResultImportBatch", back_populates="errors")


class ResultPublication(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "result_publications"

    examination_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("examinations.id", ondelete="CASCADE"), nullable=False, index=True)
    class_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    published_by_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notification_dispatched: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ResultNotificationJob(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "result_notification_jobs"

    publication_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("result_publications.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("communication_campaigns.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)
