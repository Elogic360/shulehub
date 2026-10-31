from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token, create_refresh_token, decode_token
from app.schemas.auth import LoginRequest, TokenResponse, RegisterSchoolRequest, RegisterStaffRequest, RefreshTokenRequest
from app.models.identity import User, School, SchoolMembership, MembershipRole, Role, RoleType, SchoolType
from app.models.academic import AcademicLevel, AcademicYear, AcademicTerm
from app.models.operations import Subscription, SubscriptionPlan, SubscriptionStatus
from app.utils.phone import normalize_tanzanian_phone
from app.api.deps import get_current_user, get_current_school

router = APIRouter()


@router.post("/register-school", response_model=TokenResponse)
def register_school(req: RegisterSchoolRequest, db: Session = Depends(get_db)):
    """
    Registers a new private primary or secondary school with its default academic structure.
    """
    # 1. Normalize contact phone
    try:
        norm_phone = normalize_tanzanian_phone(req.contact_phone)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 2. Check duplicate code
    existing_code = db.execute(select(School).where(School.code == req.school_code)).scalar_one_or_none()
    if existing_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="School code already exists")

    # 3. Create or find User for owner
    owner_user = db.execute(select(User).where(User.phone_number == norm_phone)).scalar_one_or_none()
    if not owner_user:
        owner_user = User(
            email=str(req.contact_email),
            phone_number=norm_phone,
            full_name=req.owner_full_name,
            password_hash=hash_password(req.owner_password),
            is_active=True,
            preferred_language="sw",
        )
        db.add(owner_user)
        db.flush()

    # 4. Create School
    school = School(
        name=req.school_name,
        code=req.school_code.upper(),
        school_type=req.school_type,
        registration_number=req.registration_number,
        contact_email=str(req.contact_email),
        contact_phone=norm_phone,
        region=req.region,
        district=req.district,
        is_verified=True,  # Default verified in local dev
        is_active=True,
    )
    db.add(school)
    db.flush()

    # 5. Link Owner Role
    owner_role = db.execute(select(Role).where(Role.name == RoleType.SCHOOL_OWNER.value)).scalar_one_or_none()
    membership = SchoolMembership(school_id=school.id, user_id=owner_user.id, is_active=True)
    db.add(membership)
    db.flush()

    if owner_role:
        db.add(MembershipRole(membership_id=membership.id, role_id=owner_role.id))

    # 6. Configure Default Academic Levels based on School Type
    if req.school_type == SchoolType.PRIMARY:
        default_levels = [
            ("Standard 1", "STD_1", 1),
            ("Standard 2", "STD_2", 2),
            ("Standard 3", "STD_3", 3),
            ("Standard 4", "STD_4", 4),
            ("Standard 5", "STD_5", 5),
            ("Standard 6", "STD_6", 6),
        ]
    elif req.school_type == SchoolType.SECONDARY:
        default_levels = [
            ("Form 1", "FORM_1", 1),
            ("Form 2", "FORM_2", 2),
            ("Form 3", "FORM_3", 3),
            ("Form 4", "FORM_4", 4),
        ]
    else:  # COMBINED
        default_levels = [
            ("Standard 1", "STD_1", 1),
            ("Standard 2", "STD_2", 2),
            ("Standard 3", "STD_3", 3),
            ("Standard 4", "STD_4", 4),
            ("Standard 5", "STD_5", 5),
            ("Standard 6", "STD_6", 6),
            ("Form 1", "FORM_1", 7),
            ("Form 2", "FORM_2", 8),
            ("Form 3", "FORM_3", 9),
            ("Form 4", "FORM_4", 10),
        ]

    for name, code, order in default_levels:
        st = "PRIMARY" if "Standard" in name else "SECONDARY"
        db.add(AcademicLevel(school_id=school.id, name=name, code=code, sequence_order=order, school_type=st))

    # 7. Create Default Academic Year (2026) and Terms
    curr_year = AcademicYear(
        school_id=school.id,
        name="2026",
        start_date=date(2026, 1, 12),
        end_date=date(2026, 12, 4),
        is_current=True,
    )
    db.add(curr_year)
    db.flush()

    db.add(AcademicTerm(school_id=school.id, academic_year_id=curr_year.id, name="Term 1", term_number=1, start_date=date(2026, 1, 12), end_date=date(2026, 6, 12), is_current=True))
    db.add(AcademicTerm(school_id=school.id, academic_year_id=curr_year.id, name="Term 2", term_number=2, start_date=date(2026, 7, 6), end_date=date(2026, 12, 4), is_current=False))

    # 8. Create Trial Subscription
    plan = db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == "STANDARD_TZ")).scalar_one_or_none()
    if plan:
        sub = Subscription(
            school_id=school.id,
            plan_id=plan.id,
            status=SubscriptionStatus.TRIAL,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            sms_credits_remaining=500,
        )
        db.add(sub)

    db.commit()

    # 9. Return JWT Tokens
    token_data = {"sub": str(owner_user.id), "school_id": str(school.id)}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(owner_user.id),
            "email": owner_user.email,
            "phone_number": owner_user.phone_number,
            "full_name": owner_user.full_name,
            "roles": [RoleType.SCHOOL_OWNER.value],
            "school_id": str(school.id),
            "school_name": school.name,
            "school_type": school.school_type.value,
        },
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates user via email or Tanzanian phone number.
    """
    user = None
    identifier = req.username.strip()

    # Try email lookup
    if "@" in identifier:
        user = db.execute(select(User).where(User.email == identifier.lower())).scalar_one_or_none()

    # Try phone lookup
    if not user:
        try:
            norm_phone = normalize_tanzanian_phone(identifier)
            user = db.execute(select(User).where(User.phone_number == norm_phone)).scalar_one_or_none()
        except ValueError:
            pass

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    # Determine school context
    school = None
    roles = []
    if user.is_superadmin:
        roles.append(RoleType.SUPER_ADMIN.value)
    else:
        # Fetch memberships
        query = select(SchoolMembership).where(SchoolMembership.user_id == user.id, SchoolMembership.is_active == True)
        if req.school_id:
            query = query.where(SchoolMembership.school_id == req.school_id)
        membership = db.execute(query).scalars().first()

        if membership:
            school = db.execute(select(School).where(School.id == membership.school_id)).scalar_one_or_none()
            roles = [mr.role.name for mr in membership.membership_roles]

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    token_data = {"sub": str(user.id), "school_id": str(school.id) if school else None}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "phone_number": user.phone_number,
            "full_name": user.full_name,
            "roles": roles,
            "is_superadmin": user.is_superadmin,
            "school_id": str(school.id) if school else None,
            "school_name": school.name if school else None,
            "school_type": school.school_type.value if school else None,
            "preferred_language": user.preferred_language,
        },
    )


@router.post("/register-staff")
def register_staff(
    req: RegisterStaffRequest,
    current_user: User = Depends(get_current_user),
    school: Optional[School] = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    """
    Registers a staff member (School Admin or Class Teacher) for the current school.
    """
    if not school:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="School context required")

    try:
        norm_phone = normalize_tanzanian_phone(req.phone_number)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    user = db.execute(select(User).where(User.phone_number == norm_phone)).scalar_one_or_none()
    if not user:
        user = User(
            email=str(req.email) if req.email else None,
            phone_number=norm_phone,
            full_name=req.full_name,
            password_hash=hash_password(req.password),
            preferred_language=req.preferred_language,
        )
        db.add(user)
        db.flush()

    role = db.execute(select(Role).where(Role.name == req.role_name)).scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Role {req.role_name} not found")

    membership = db.execute(
        select(SchoolMembership).where(
            SchoolMembership.school_id == school.id,
            SchoolMembership.user_id == user.id,
        )
    ).scalar_one_or_none()

    if not membership:
        membership = SchoolMembership(school_id=school.id, user_id=user.id, is_active=True)
        db.add(membership)
        db.flush()

    link = db.execute(
        select(MembershipRole).where(
            MembershipRole.membership_id == membership.id,
            MembershipRole.role_id == role.id,
        )
    ).scalar_one_or_none()

    if not link:
        db.add(MembershipRole(membership_id=membership.id, role_id=role.id))

    db.commit()
    return {"status": "success", "user_id": str(user.id), "full_name": user.full_name, "role": role.name}


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
    school: Optional[School] = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    """Returns currently authenticated user profile and active school context."""
    roles = []
    if current_user.is_superadmin:
        roles.append(RoleType.SUPER_ADMIN.value)
    elif school:
        membership = db.execute(
            select(SchoolMembership).where(
                SchoolMembership.school_id == school.id,
                SchoolMembership.user_id == current_user.id,
            )
        ).scalar_one_or_none()
        if membership:
            roles = [mr.role.name for mr in membership.membership_roles]

    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "phone_number": current_user.phone_number,
        "full_name": current_user.full_name,
        "roles": roles,
        "is_superadmin": current_user.is_superadmin,
        "school": {
            "id": str(school.id),
            "name": school.name,
            "code": school.code,
            "school_type": school.school_type.value,
        } if school else None,
        "preferred_language": current_user.preferred_language,
    }
