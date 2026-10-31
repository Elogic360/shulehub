import uuid
from typing import Optional, List
from datetime import date, datetime, timezone
import enum
from sqlalchemy import String, Boolean, Date, DateTime, Integer, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Gender(str, enum.Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    PROMOTED = "PROMOTED"
    TRANSFERRED = "TRANSFERRED"
    WITHDRAWN = "WITHDRAWN"


class GuardianRelationship(str, enum.Enum):
    FATHER = "FATHER"
    MOTHER = "MOTHER"
    GUARDIAN = "GUARDIAN"
    UNCLE = "UNCLE"
    AUNT = "AUNT"
    OTHER = "OTHER"


class AcademicLevel(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "academic_levels"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Standard 1", "Form 1"
    code: Mapped[str] = mapped_column(String(50), nullable=False)   # e.g., "STD_1", "FORM_1"
    sequence_order: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    school_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "PRIMARY" or "SECONDARY"

    class_groups: Mapped[List["ClassGroup"]] = relationship("ClassGroup", back_populates="academic_level", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_school_academic_level_code"),
    )


class AcademicYear(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "academic_years"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "2026"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    terms: Mapped[List["AcademicTerm"]] = relationship("AcademicTerm", back_populates="academic_year", cascade="all, delete-orphan")
    class_groups: Mapped[List["ClassGroup"]] = relationship("ClassGroup", back_populates="academic_year", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_school_academic_year_name"),
    )


class AcademicTerm(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "academic_terms"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Term 1"
    term_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear", back_populates="terms")

    __table_args__ = (
        UniqueConstraint("academic_year_id", "term_number", name="uq_academic_year_term_number"),
    )


class ClassGroup(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "class_groups"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_level_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_levels.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Standard 1A", "Form 2B"
    stream: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., "A", "B", "East"
    capacity: Mapped[int] = mapped_column(Integer, default=50, nullable=False)

    academic_level: Mapped["AcademicLevel"] = relationship("AcademicLevel", back_populates="class_groups")
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear", back_populates="class_groups")
    teacher_assignments: Mapped[List["ClassTeacherAssignment"]] = relationship("ClassTeacherAssignment", back_populates="class_group", cascade="all, delete-orphan")
    enrollments: Mapped[List["StudentEnrollment"]] = relationship("StudentEnrollment", back_populates="class_group", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("academic_year_id", "academic_level_id", "name", name="uq_class_group_year_level_name"),
    )


class ClassTeacherAssignment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "class_teacher_assignments"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    class_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    class_group: Mapped["ClassGroup"] = relationship("ClassGroup", back_populates="teacher_assignments")

    __table_args__ = (
        UniqueConstraint("class_group_id", "teacher_user_id", "academic_year_id", name="uq_class_teacher_year"),
    )


class ClassSubjectAssignment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "class_subject_assignments"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    class_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)


class TeacherSubjectAssignment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "teacher_subject_assignments"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    class_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)


class Student(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "students"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    admission_number: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    gender: Mapped[Gender] = mapped_column(SQLEnum(Gender), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    enrollments: Mapped[List["StudentEnrollment"]] = relationship("StudentEnrollment", back_populates="student", cascade="all, delete-orphan")
    guardians: Mapped[List["StudentGuardian"]] = relationship("StudentGuardian", back_populates="student", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("school_id", "admission_number", name="uq_school_student_admission"),
    )


class StudentEnrollment(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "student_enrollments"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    class_group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("class_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    academic_year_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False, index=True)
    enrollment_status: Mapped[EnrollmentStatus] = mapped_column(SQLEnum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE, nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="enrollments")
    class_group: Mapped["ClassGroup"] = relationship("ClassGroup", back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint("student_id", "academic_year_id", name="uq_student_year_enrollment"),
    )


class Guardian(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "guardians"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    primary_phone: Mapped[str] = mapped_column(String(30), nullable=False, index=True)  # E.164 normalized (+255...)
    secondary_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    national_id_nin: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(10), default="sw", nullable=False)  # 'sw' or 'en'
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    students: Mapped[List["StudentGuardian"]] = relationship("StudentGuardian", back_populates="guardian", cascade="all, delete-orphan")
    contacts: Mapped[List["GuardianContact"]] = relationship("GuardianContact", back_populates="guardian", cascade="all, delete-orphan")
    consents: Mapped[List["GuardianConsent"]] = relationship("GuardianConsent", back_populates="guardian", cascade="all, delete-orphan")


class GuardianContact(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "guardian_contacts"

    guardian_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guardians.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_type: Mapped[str] = mapped_column(String(50), nullable=False)  # "PHONE", "EMAIL"
    contact_value: Mapped[str] = mapped_column(String(255), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    guardian: Mapped["Guardian"] = relationship("Guardian", back_populates="contacts")


class StudentGuardian(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "student_guardians"

    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    guardian_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guardians.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type: Mapped[GuardianRelationship] = mapped_column(SQLEnum(GuardianRelationship), default=GuardianRelationship.GUARDIAN, nullable=False)
    is_emergency_contact: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_fee_payer: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_receive_results: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    student: Mapped["Student"] = relationship("Student", back_populates="guardians")
    guardian: Mapped["Guardian"] = relationship("Guardian", back_populates="students")

    __table_args__ = (
        UniqueConstraint("student_id", "guardian_id", name="uq_student_guardian"),
    )


class GuardianConsent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "guardian_consents"

    guardian_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("guardians.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type: Mapped[str] = mapped_column(String(100), nullable=False)  # "SMS_COMMUNICATION", "EXAM_RESULTS", "MARKETING"
    is_granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    guardian: Mapped["Guardian"] = relationship("Guardian", back_populates="consents")
