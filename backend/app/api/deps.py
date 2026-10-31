import uuid
from typing import Optional, List, Generator
from fastapi import Depends, HTTPException, status, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db, set_rls_tenant_context
from app.core.security import decode_token
from app.models.identity import (
    User,
    School,
    SchoolMembership,
    MembershipRole,
    RolePermission,
    Permission,
    RoleType,
)
from app.models.academic import ClassTeacherAssignment

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise credentials_exception

    user_id_str = payload["sub"]
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")
    return user


def get_current_school(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_school_id: Optional[str] = Header(None, alias="X-School-ID"),
) -> Optional[School]:
    """
    Extracts and validates school tenant context.
    Sets PostgreSQL session Row-Level Security context (app.current_school_id).
    """
    school = None
    if x_school_id:
        try:
            school_uuid = uuid.UUID(x_school_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-School-ID header format")

        if user.is_superadmin:
            school = db.execute(select(School).where(School.id == school_uuid)).scalar_one_or_none()
        else:
            membership = db.execute(
                select(SchoolMembership).where(
                    SchoolMembership.school_id == school_uuid,
                    SchoolMembership.user_id == user.id,
                    SchoolMembership.is_active == True,
                )
            ).scalar_one_or_none()
            if not membership:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to specified school denied")
            school = db.execute(select(School).where(School.id == school_uuid)).scalar_one_or_none()

    elif not user.is_superadmin:
        # Fallback to user's first active membership
        membership = db.execute(
            select(SchoolMembership)
            .where(SchoolMembership.user_id == user.id, SchoolMembership.is_active == True)
        ).scalars().first()
        if membership:
            school = db.execute(select(School).where(School.id == membership.school_id)).scalar_one_or_none()

    # Set PostgreSQL RLS context
    set_rls_tenant_context(db, school.id if school else None)
    return school


class PermissionChecker:
    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(
        self,
        user: User = Depends(get_current_user),
        school: Optional[School] = Depends(get_current_school),
        db: Session = Depends(get_db),
    ) -> bool:
        if user.is_superadmin:
            return True

        if not school:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="School context required for this operation")

        # Find user's membership in the school
        membership = db.execute(
            select(SchoolMembership).where(
                SchoolMembership.school_id == school.id,
                SchoolMembership.user_id == user.id,
                SchoolMembership.is_active == True,
            )
        ).scalar_one_or_none()

        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active membership in school")

        # Query assigned permissions across roles
        has_perm = db.execute(
            select(Permission.id)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(MembershipRole, MembershipRole.role_id == RolePermission.role_id)
            .where(
                MembershipRole.membership_id == membership.id,
                Permission.code == self.required_permission,
            )
        ).first()

        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {self.required_permission} required",
            )
        return True


def verify_class_teacher_access(
    class_group_id: uuid.UUID,
    user: User,
    school_id: uuid.UUID,
    db: Session,
) -> bool:
    """
    Ensures that a teacher can only manage their assigned class,
    while School Owners / Admins have broader access.
    """
    if user.is_superadmin:
        return True

    # Check if user is School Owner or School Admin
    membership = db.execute(
        select(SchoolMembership).where(
            SchoolMembership.school_id == school_id,
            SchoolMembership.user_id == user.id,
            SchoolMembership.is_active == True,
        )
    ).scalar_one_or_none()

    if not membership:
        return False

    roles = [mr.role.name for mr in membership.membership_roles]
    if RoleType.SCHOOL_OWNER.value in roles or RoleType.SCHOOL_ADMIN.value in roles:
        return True

    # Check ClassTeacherAssignment
    assignment = db.execute(
        select(ClassTeacherAssignment).where(
            ClassTeacherAssignment.class_group_id == class_group_id,
            ClassTeacherAssignment.teacher_user_id == user.id,
            ClassTeacherAssignment.is_active == True,
        )
    ).scalar_one_or_none()

    return assignment is not None
