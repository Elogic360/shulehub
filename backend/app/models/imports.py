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
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class ImportWorkflowType(str, enum.Enum):
    STUDENT_REGISTRATION = "STUDENT_REGISTRATION"
    EXAM_RESULTS = "EXAM_RESULTS"
    FEE_STRUCTURES = "FEE_STRUCTURES"
    FEE_BALANCES = "FEE_BALANCES"


class ImportStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PARSING = "PARSING"
    VALIDATING = "VALIDATING"
    PREVIEW_READY = "PREVIEW_READY"
    APPROVED = "APPROVED"
    COMMITTING = "COMMITTING"
    COMMITTED = "COMMITTED"
    FAILED = "FAILED"
    REVERTED = "REVERTED"


class ImportRowStatus(str, enum.Enum):
    PENDING = "PENDING"
    VALID = "VALID"
    WARNING = "WARNING"
    ERROR = "ERROR"
    COMMITTED = "COMMITTED"
    REVERTED = "REVERTED"


class ImportBatch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "import_batches"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    class_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("class_groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    workflow_type: Mapped[ImportWorkflowType] = mapped_column(
        SQLEnum(ImportWorkflowType),
        nullable=False,
        index=True,
    )
    status: Mapped[ImportStatus] = mapped_column(
        SQLEnum(ImportStatus),
        default=ImportStatus.UPLOADED,
        nullable=False,
        index=True,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    approved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    total_rows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_records_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_records_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unchanged_records_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_records_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_records_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    metadata_info: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    column_mapping: Mapped[Dict[str, str]] = mapped_column(JSONB, default=dict, nullable=False)

    committed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reverted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reverted_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    files: Mapped[List["ImportBatchFile"]] = relationship(
        "ImportBatchFile",
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    staging_rows: Mapped[List["ImportStagingRow"]] = relationship(
        "ImportStagingRow",
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    validation_errors: Mapped[List["ImportValidationError"]] = relationship(
        "ImportValidationError",
        back_populates="batch",
        cascade="all, delete-orphan",
    )
    change_records: Mapped[List["ImportChangeRecord"]] = relationship(
        "ImportChangeRecord",
        back_populates="batch",
        cascade="all, delete-orphan",
    )


class ImportBatchFile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "import_batch_files"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    batch: Mapped["ImportBatch"] = relationship("ImportBatch", back_populates="files")


class ImportStagingRow(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "import_staging_rows"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    raw_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    mapped_data: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[ImportRowStatus] = mapped_column(
        SQLEnum(ImportRowStatus),
        default=ImportRowStatus.PENDING,
        nullable=False,
        index=True,
    )
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    action_type: Mapped[str] = mapped_column(String(20), default="INSERT", nullable=False)  # INSERT, UPDATE, SKIP
    target_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    batch: Mapped["ImportBatch"] = relationship("ImportBatch", back_populates="staging_rows")


class ImportValidationError(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "import_validation_errors"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    column_name: Mapped[str] = mapped_column(String(100), nullable=False)
    error_code: Mapped[str] = mapped_column(String(50), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    raw_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    batch: Mapped["ImportBatch"] = relationship("ImportBatch", back_populates="validation_errors")


class ImportChangeRecord(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "import_change_records"

    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Student, ExamResult, FeeInvoice
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # INSERT, UPDATE
    before_state: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)

    batch: Mapped["ImportBatch"] = relationship("ImportBatch", back_populates="change_records")
