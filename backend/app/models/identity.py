import uuid
from typing import Optional, List
from datetime import datetime, timezone
import enum
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class SchoolType(str, enum.Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    COMBINED = "COMBINED"


class RoleType(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    SCHOOL_OWNER = "SCHOOL_OWNER"
    SCHOOL_ADMIN = "SCHOOL_ADMIN"
    CLASS_TEACHER = "CLASS_TEACHER"
    PARENT = "PARENT"


class School(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "schools"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    school_type: Mapped[SchoolType] = mapped_column(SQLEnum(SchoolType), nullable=False)
    registration_number: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(30), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False, default="Dar es Salaam")
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    branches: Mapped[List["SchoolBranch"]] = relationship("SchoolBranch", back_populates="school", cascade="all, delete-orphan")
    memberships: Mapped[List["SchoolMembership"]] = relationship("SchoolMembership", back_populates="school", cascade="all, delete-orphan")


class SchoolBranch(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "school_branches"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_main: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    school: Mapped["School"] = relationship("School", back_populates="branches")

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_school_branch_code"),
    )


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    phone_number: Mapped[str] = mapped_column(String(30), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(10), default="sw", nullable=False)  # 'sw' (Kiswahili) or 'en'
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    memberships: Mapped[List["SchoolMembership"]] = relationship("SchoolMembership", back_populates="user", cascade="all, delete-orphan")


class Role(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    role_permissions: Mapped[List["RolePermission"]] = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")


class Permission(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "permissions"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    module: Mapped[str] = mapped_column(String(100), nullable=False)


class RolePermission(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, index=True)

    role: Mapped["Role"] = relationship("Role", back_populates="role_permissions")
    permission: Mapped["Permission"] = relationship("Permission")

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )


class SchoolMembership(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "school_memberships"

    school_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("school_branches.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    school: Mapped["School"] = relationship("School", back_populates="memberships")
    user: Mapped["User"] = relationship("User", back_populates="memberships")
    membership_roles: Mapped[List["MembershipRole"]] = relationship("MembershipRole", back_populates="membership", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("school_id", "user_id", name="uq_school_user_membership"),
    )


class MembershipRole(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "membership_roles"

    membership_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("school_memberships.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, index=True)

    membership: Mapped["SchoolMembership"] = relationship("SchoolMembership", back_populates="membership_roles")
    role: Mapped["Role"] = relationship("Role")

    __table_args__ = (
        UniqueConstraint("membership_id", "role_id", name="uq_membership_role"),
    )


class SchoolRegistrationInvitation(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "school_registration_invitations"

    token: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    target_school_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    target_contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    target_contact_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    registered_school_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_by: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    registered_school: Mapped[Optional["School"]] = relationship("School", foreign_keys=[registered_school_id])
