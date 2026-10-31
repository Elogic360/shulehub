import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import enum
from sqlalchemy import (
    String,
    Boolean,
    DateTime,
    Integer,
    Numeric,
    Text,
    ForeignKey,
    Enum as SQLEnum,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class NectaExamType(str, enum.Enum):
    FTNA = "FTNA"  # Form Two National Assessment
    CSEE = "CSEE"  # Certificate of Secondary Education Examination


class NectaMatchStatus(str, enum.Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    MATCHED = "MATCHED"
    REJECTED = "REJECTED"


class NectaExamination(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "necta_examinations"

    school_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    exam_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    exam_type: Mapped[NectaExamType] = mapped_column(
        SQLEnum(NectaExamType),
        nullable=False,
        index=True,
    )
    center_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # e.g., "S.0101"
    center_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(String(500), nullable=False)
    source_provenance: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    candidates: Mapped[List["NectaCandidate"]] = relationship(
        "NectaCandidate",
        back_populates="examination",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("exam_year", "exam_type", "center_number", name="uq_necta_exam_center"),
    )


class NectaCandidate(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "necta_candidates"

    examination_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("necta_examinations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    index_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # e.g., "S0101/0001"
    candidate_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sex: Mapped[str] = mapped_column(String(10), nullable=False)  # M / F
    division: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # e.g., "I", "II", "III", "IV", "0"
    points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    examination: Mapped["NectaExamination"] = relationship("NectaExamination", back_populates="candidates")
    subjects: Mapped[List["NectaCandidateSubject"]] = relationship(
        "NectaCandidateSubject",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )
    matches: Mapped[List["NectaStudentMatch"]] = relationship(
        "NectaStudentMatch",
        back_populates="candidate",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("examination_id", "index_number", name="uq_necta_candidate_index"),
    )


class NectaCandidateSubject(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "necta_candidate_subjects"

    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("necta_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_code: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "CIV", "HIST", "B/MATH"
    subject_name: Mapped[str] = mapped_column(String(100), nullable=False)
    grade: Mapped[str] = mapped_column(String(5), nullable=False)  # A, B, C, D, F

    candidate: Mapped["NectaCandidate"] = relationship("NectaCandidate", back_populates="subjects")


class NectaStudentMatch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "necta_student_matches"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("necta_candidates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    match_confidence: Mapped[float] = mapped_column(Numeric(4, 3), default=1.000, nullable=False)  # 0.000 to 1.000
    status: Mapped[NectaMatchStatus] = mapped_column(
        SQLEnum(NectaMatchStatus),
        default=NectaMatchStatus.PENDING_REVIEW,
        nullable=False,
        index=True,
    )
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    candidate: Mapped["NectaCandidate"] = relationship("NectaCandidate", back_populates="matches")
    student: Mapped["Student"] = relationship("Student")

    __table_args__ = (
        UniqueConstraint("candidate_id", "student_id", name="uq_necta_candidate_student_match"),
    )


class NectaFetchError(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "necta_fetch_errors"

    url: Mapped[str] = mapped_column(String(500), nullable=False)
    error_type: Mapped[str] = mapped_column(String(100), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    center_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    exam_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
