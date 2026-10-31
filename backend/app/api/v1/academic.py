import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_school, PermissionChecker
from app.models.identity import User, School, RoleType, SchoolMembership
from app.models.academic import (
    AcademicYear,
    AcademicTerm,
    AcademicLevel,
    ClassGroup,
    ClassTeacherAssignment,
)
from app.schemas.academic import (
    AcademicYearCreate,
    AcademicTermCreate,
    AcademicLevelCreate,
    ClassGroupCreate,
    ClassTeacherAssignRequest,
)

router = APIRouter()


@router.get("/years")
def list_academic_years(
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")
    years = db.execute(select(AcademicYear).where(AcademicYear.school_id == school.id).order_by(AcademicYear.name.desc())).scalars().all()
    return years


@router.post("/years")
def create_academic_year(
    req: AcademicYearCreate,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("academic:manage_structure")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    existing = db.execute(select(AcademicYear).where(AcademicYear.school_id == school.id, AcademicYear.name == req.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail=f"Academic year {req.name} already exists")

    year = AcademicYear(
        school_id=school.id,
        name=req.name,
        start_date=req.start_date,
        end_date=req.end_date,
        is_current=req.is_current,
    )
    db.add(year)
    db.commit()
    db.refresh(year)
    return year


@router.get("/terms")
def list_academic_terms(
    academic_year_id: Optional[uuid.UUID] = None,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")
    query = select(AcademicTerm).where(AcademicTerm.school_id == school.id)
    if academic_year_id:
        query = query.where(AcademicTerm.academic_year_id == academic_year_id)
    terms = db.execute(query.order_by(AcademicTerm.term_number.asc())).scalars().all()
    return terms


@router.post("/terms")
def create_academic_term(
    req: AcademicTermCreate,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("academic:manage_structure")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    term = AcademicTerm(
        school_id=school.id,
        academic_year_id=req.academic_year_id,
        name=req.name,
        term_number=req.term_number,
        start_date=req.start_date,
        end_date=req.end_date,
        is_current=req.is_current,
    )
    db.add(term)
    db.commit()
    db.refresh(term)
    return term


@router.get("/levels")
def list_academic_levels(
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")
    levels = db.execute(select(AcademicLevel).where(AcademicLevel.school_id == school.id).order_by(AcademicLevel.sequence_order.asc())).scalars().all()
    return levels


@router.post("/levels")
def create_academic_level(
    req: AcademicLevelCreate,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("academic:manage_structure")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    level = AcademicLevel(
        school_id=school.id,
        name=req.name,
        code=req.code,
        sequence_order=req.sequence_order,
        school_type=req.school_type,
    )
    db.add(level)
    db.commit()
    db.refresh(level)
    return level


@router.get("/classes")
def list_class_groups(
    academic_year_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    """
    Lists class groups. For Class Teachers, lists only assigned classes.
    For School Owners and School Admins, lists all classes.
    """
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    query = select(ClassGroup).where(ClassGroup.school_id == school.id)
    if academic_year_id:
        query = query.where(ClassGroup.academic_year_id == academic_year_id)

    # Check user role in this school
    membership = db.execute(
        select(SchoolMembership).where(
            SchoolMembership.school_id == school.id,
            SchoolMembership.user_id == current_user.id,
        )
    ).scalar_one_or_none()

    is_class_teacher_only = False
    if membership and not current_user.is_superadmin:
        roles = [mr.role.name for mr in membership.membership_roles]
        if RoleType.CLASS_TEACHER.value in roles and RoleType.SCHOOL_OWNER.value not in roles and RoleType.SCHOOL_ADMIN.value not in roles:
            is_class_teacher_only = True

    if is_class_teacher_only:
        query = query.join(
            ClassTeacherAssignment,
            ClassTeacherAssignment.class_group_id == ClassGroup.id,
        ).where(
            ClassTeacherAssignment.teacher_user_id == current_user.id,
            ClassTeacherAssignment.is_active == True,
        )

    classes = db.execute(query.order_by(ClassGroup.name.asc())).scalars().all()
    results = []
    for c in classes:
        teacher_asgn = db.execute(
            select(ClassTeacherAssignment)
            .where(ClassTeacherAssignment.class_group_id == c.id, ClassTeacherAssignment.is_active == True)
        ).scalar_one_or_none()
        teacher_user = None
        if teacher_asgn:
            teacher_user = db.execute(select(User).where(User.id == teacher_asgn.teacher_user_id)).scalar_one_or_none()

        results.append({
            "id": str(c.id),
            "name": c.name,
            "stream": c.stream,
            "capacity": c.capacity,
            "academic_level_id": str(c.academic_level_id),
            "academic_year_id": str(c.academic_year_id),
            "academic_level_name": c.academic_level.name if c.academic_level else None,
            "teacher": {
                "id": str(teacher_user.id),
                "full_name": teacher_user.full_name,
                "phone_number": teacher_user.phone_number,
            } if teacher_user else None,
        })
    return results


@router.post("/classes")
def create_class_group(
    req: ClassGroupCreate,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("academic:manage_classes")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    class_group = ClassGroup(
        school_id=school.id,
        academic_level_id=req.academic_level_id,
        academic_year_id=req.academic_year_id,
        name=req.name,
        stream=req.stream,
        capacity=req.capacity,
    )
    db.add(class_group)
    db.commit()
    db.refresh(class_group)
    return class_group


@router.post("/classes/assign-teacher")
def assign_class_teacher(
    req: ClassTeacherAssignRequest,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("academic:assign_teachers")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    # Deactivate existing active assignment
    existing = db.execute(
        select(ClassTeacherAssignment).where(
            ClassTeacherAssignment.class_group_id == req.class_group_id,
            ClassTeacherAssignment.academic_year_id == req.academic_year_id,
            ClassTeacherAssignment.is_active == True,
        )
    ).scalar_one_or_none()
    if existing:
        existing.is_active = False

    new_assignment = ClassTeacherAssignment(
        school_id=school.id,
        class_group_id=req.class_group_id,
        teacher_user_id=req.teacher_user_id,
        academic_year_id=req.academic_year_id,
        is_active=True,
    )
    db.add(new_assignment)
    db.commit()
    return {"status": "success", "message": "Class teacher assigned successfully"}
