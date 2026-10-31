import csv
import io
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import select
import openpyxl

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_school, PermissionChecker, verify_class_teacher_access
from app.models.identity import User, School
from app.models.academic import (
    Student,
    StudentEnrollment,
    Guardian,
    StudentGuardian,
    ClassGroup,
    Gender,
    GuardianRelationship,
    EnrollmentStatus,
    GuardianContactHistory,
)
from app.models.ussd import UssdOtpVerification
from app.services.import_engine import generate_unique_ussd_access_id
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    GuardianCreate,
    GuardianLinkRequest,
)
from app.utils.phone import normalize_tanzanian_phone

router = APIRouter()


@router.get("")
def list_students(
    class_group_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("student:view")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    if class_group_id and not verify_class_teacher_access(class_group_id, current_user, school.id, db):
        raise HTTPException(status_code=403, detail="Access denied to this class")

    query = select(Student).where(Student.school_id == school.id, Student.is_active == True)

    if class_group_id:
        query = query.join(StudentEnrollment, StudentEnrollment.student_id == Student.id).where(
            StudentEnrollment.class_group_id == class_group_id,
            StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE,
        )

    if search:
        s = f"%{search.strip()}%"
        query = query.where(
            (Student.first_name.ilike(s)) | (Student.last_name.ilike(s)) | (Student.admission_number.ilike(s))
        )

    students = db.execute(query.order_by(Student.last_name.asc())).scalars().all()
    results = []
    for st in students:
        curr_enrollment = db.execute(
            select(StudentEnrollment)
            .where(StudentEnrollment.student_id == st.id, StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE)
        ).scalar_one_or_none()
        class_name = curr_enrollment.class_group.name if curr_enrollment and curr_enrollment.class_group else None

        guardian_links = db.execute(
            select(StudentGuardian).where(StudentGuardian.student_id == st.id)
        ).scalars().all()

        guardians_data = []
        for gl in guardian_links:
            g = gl.guardian
            guardians_data.append({
                "id": str(g.id),
                "full_name": g.full_name,
                "primary_phone": g.primary_phone,
                "relationship": gl.relationship_type.value,
                "is_fee_payer": gl.is_fee_payer,
                "can_receive_results": gl.can_receive_results,
            })

        # Ensure student has a numeric USSD access ID
        if not st.ussd_access_id:
            st.ussd_access_id = generate_unique_ussd_access_id(db)
            db.flush()

        results.append({
            "id": str(st.id),
            "admission_number": st.admission_number,
            "ussd_access_id": st.ussd_access_id,
            "first_name": st.first_name,
            "middle_name": st.middle_name,
            "last_name": st.last_name,
            "gender": st.gender.value,
            "date_of_birth": str(st.date_of_birth) if st.date_of_birth else None,
            "class_group_id": str(curr_enrollment.class_group_id) if curr_enrollment else None,
            "class_name": class_name,
            "guardians": guardians_data,
        })
    return results


@router.post("")
def create_student(
    req: StudentCreate,
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("student:create")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    # Enforce class teacher scope check
    if not verify_class_teacher_access(req.class_group_id, current_user, school.id, db):
        raise HTTPException(status_code=403, detail="Cannot register students into classes you are not assigned to")

    existing_adm = db.execute(
        select(Student).where(Student.school_id == school.id, Student.admission_number == req.admission_number)
    ).scalar_one_or_none()
    if existing_adm:
        raise HTTPException(status_code=400, detail=f"Admission number {req.admission_number} already in use")

    student = Student(
        school_id=school.id,
        admission_number=req.admission_number.strip().upper(),
        first_name=req.first_name.strip(),
        middle_name=req.middle_name.strip() if req.middle_name else None,
        last_name=req.last_name.strip(),
        gender=req.gender,
        date_of_birth=req.date_of_birth,
        is_active=True,
    )
    db.add(student)
    db.flush()

    enrollment = StudentEnrollment(
        school_id=school.id,
        student_id=student.id,
        class_group_id=req.class_group_id,
        academic_year_id=req.academic_year_id,
        enrollment_status=EnrollmentStatus.ACTIVE,
    )
    db.add(enrollment)

    # If guardian info provided, register and link
    if req.guardian:
        try:
            norm_phone = normalize_tanzanian_phone(req.guardian.primary_phone)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        guardian = db.execute(
            select(Guardian).where(Guardian.school_id == school.id, Guardian.primary_phone == norm_phone)
        ).scalar_one_or_none()

        if not guardian:
            guardian = Guardian(
                school_id=school.id,
                full_name=req.guardian.full_name.strip(),
                primary_phone=norm_phone,
                secondary_phone=req.guardian.secondary_phone,
                email=str(req.guardian.email) if req.guardian.email else None,
                preferred_language=req.guardian.preferred_language,
                is_verified=False,
            )
            db.add(guardian)
            db.flush()

        link = StudentGuardian(
            student_id=student.id,
            guardian_id=guardian.id,
            relationship_type=req.guardian.relationship_type,
            is_fee_payer=req.guardian.is_fee_payer,
            can_receive_results=req.guardian.can_receive_results,
        )
        db.add(link)

    db.commit()
    return {"status": "success", "student_id": str(student.id), "admission_number": student.admission_number}


@router.post("/import")
async def import_students_file(
    class_group_id: uuid.UUID,
    academic_year_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("student:import")),
):
    """
    Imports student rosters from CSV or Excel (.xlsx) files.
    Performs validation before commit: detects duplicates, invalid formats, missing fields.
    """
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    if not verify_class_teacher_access(class_group_id, current_user, school.id, db):
        raise HTTPException(status_code=403, detail="Cannot import into a class you are not assigned to")

    content = await file.read()
    filename = file.filename or ""

    rows_data = []
    if filename.endswith(".csv") or file.content_type == "text/csv":
        text_stream = io.StringIO(content.decode("utf-8-sig", errors="ignore"))
        reader = csv.DictReader(text_stream)
        for r in reader:
            rows_data.append(r)
    elif filename.endswith(".xlsx"):
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        sheet = wb.active
        headers = [cell.value for cell in sheet[1]]
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if any(row):
                row_dict = {str(headers[i]): row[i] for i in range(len(headers)) if headers[i]}
                rows_data.append(row_dict)
    else:
        raise HTTPException(status_code=400, detail="Supported file formats: .csv, .xlsx")

    created_count = 0
    errors = []

    for idx, row in enumerate(rows_data, start=2):
        adm_no = str(row.get("admission_number") or row.get("Admission Number") or "").strip()
        first_name = str(row.get("first_name") or row.get("First Name") or "").strip()
        last_name = str(row.get("last_name") or row.get("Last Name") or "").strip()
        gender_str = str(row.get("gender") or row.get("Gender") or "MALE").strip().upper()
        parent_phone = str(row.get("parent_phone") or row.get("Guardian Phone") or "").strip()
        parent_name = str(row.get("parent_name") or row.get("Guardian Name") or "").strip()

        if not adm_no or not first_name or not last_name:
            errors.append(f"Row {idx}: Missing mandatory fields (admission_number, first_name, or last_name)")
            continue

        gender = Gender.FEMALE if gender_str in ("F", "FEMALE") else Gender.MALE

        # Check existing admission
        existing = db.execute(
            select(Student).where(Student.school_id == school.id, Student.admission_number == adm_no)
        ).scalar_one_or_none()

        if existing:
            errors.append(f"Row {idx}: Admission number {adm_no} already exists")
            continue

        student = Student(
            school_id=school.id,
            admission_number=adm_no.upper(),
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            is_active=True,
        )
        db.add(student)
        db.flush()

        enrollment = StudentEnrollment(
            school_id=school.id,
            student_id=student.id,
            class_group_id=class_group_id,
            academic_year_id=academic_year_id,
            enrollment_status=EnrollmentStatus.ACTIVE,
        )
        db.add(enrollment)

        # Parent link if provided
        if parent_phone and parent_name:
            try:
                norm_phone = normalize_tanzanian_phone(parent_phone)
                guardian = db.execute(
                    select(Guardian).where(Guardian.school_id == school.id, Guardian.primary_phone == norm_phone)
                ).scalar_one_or_none()

                if not guardian:
                    guardian = Guardian(
                        school_id=school.id,
                        full_name=parent_name,
                        primary_phone=norm_phone,
                    )
                    db.add(guardian)
                    db.flush()

                db.add(StudentGuardian(
                    student_id=student.id,
                    guardian_id=guardian.id,
                    relationship_type=GuardianRelationship.GUARDIAN,
                    is_fee_payer=True,
                    can_receive_results=True,
                ))
            except Exception as e:
                errors.append(f"Row {idx}: Failed normalizing phone '{parent_phone}': {e}")

        created_count += 1

    db.commit()
    return {
        "status": "success",
        "imported_count": created_count,
        "errors_count": len(errors),
        "errors": errors,
    }


@router.post("/guardians")
def register_guardian(
    req: GuardianCreate,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("guardian:create")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    try:
        norm_phone = normalize_tanzanian_phone(req.primary_phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    guardian = db.execute(
        select(Guardian).where(Guardian.school_id == school.id, Guardian.primary_phone == norm_phone)
    ).scalar_one_or_none()

    if not guardian:
        guardian = Guardian(
            school_id=school.id,
            full_name=req.full_name,
            primary_phone=norm_phone,
            secondary_phone=req.secondary_phone,
            email=str(req.email) if req.email else None,
            preferred_language=req.preferred_language,
        )
        db.add(guardian)
        db.commit()
        db.refresh(guardian)

    return guardian


@router.post("/link-guardian")
def link_guardian_to_student(
    req: GuardianLinkRequest,
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("guardian:link")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    student = db.execute(select(Student).where(Student.id == req.student_id, Student.school_id == school.id)).scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    guardian = db.execute(select(Guardian).where(Guardian.id == req.guardian_id, Guardian.school_id == school.id)).scalar_one_or_none()
    if not guardian:
        raise HTTPException(status_code=404, detail="Guardian not found")

    existing_link = db.execute(
        select(StudentGuardian).where(
            StudentGuardian.student_id == student.id,
            StudentGuardian.guardian_id == guardian.id,
        )
    ).scalar_one_or_none()

    if not existing_link:
        db.add(StudentGuardian(
            student_id=student.id,
            guardian_id=guardian.id,
            relationship_type=req.relationship_type,
            is_fee_payer=req.is_fee_payer,
            can_receive_results=req.can_receive_results,
        ))
    else:
        existing_link.relationship_type = req.relationship_type
        existing_link.is_fee_payer = req.is_fee_payer
        existing_link.can_receive_results = req.can_receive_results

    db.commit()
    return {"status": "success", "message": "Guardian linked successfully"}


@router.post("/guardians/{guardian_id}/change-phone")
def change_guardian_phone(
    guardian_id: uuid.UUID,
    new_phone: str = Form(...),
    change_reason: str = Form(...),
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("guardian:edit")),
):
    """
    Records an auditable guardian phone number change, preserves contact history,
    and invalidates active USSD verification tokens.
    """
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    try:
        norm_phone = normalize_tanzanian_phone(new_phone)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    guardian = db.execute(select(Guardian).where(Guardian.id == guardian_id)).scalar_one_or_none()
    if not guardian:
        raise HTTPException(status_code=404, detail="Guardian not found")

    old_phone = guardian.primary_phone

    # Record history
    history = GuardianContactHistory(
        guardian_id=guardian.id,
        school_id=school.id,
        previous_phone=old_phone,
        new_phone=norm_phone,
        change_reason=change_reason,
        changed_by_user_id=current_user.id,
        verification_state="PENDING_REVERIFICATION",
    )
    db.add(history)

    # Invalidate existing USSD OTP tokens for this phone/guardian
    active_tokens = db.execute(
        select(UssdOtpVerification).where(
            UssdOtpVerification.guardian_id == guardian.id,
            UssdOtpVerification.is_used == False,
        )
    ).scalars().all()
    for tok in active_tokens:
        tok.is_used = True

    guardian.primary_phone = norm_phone
    guardian.is_verified = False  # Requires re-verification
    db.commit()

    return {
        "status": "success",
        "message": f"Phone changed from {old_phone} to {norm_phone}. USSD sessions invalidated.",
        "previous_phone": old_phone,
        "new_phone": norm_phone,
    }


@router.post("/{student_id}/lifecycle-status")
def update_student_lifecycle_status(
    student_id: uuid.UUID,
    enrollment_status: EnrollmentStatus = Form(...),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("student:edit")),
):
    """
    Reconciles student academic lifecycle status (PROMOTED, TRANSFERRED, WITHDRAWN, COMPLETED).
    Preserves historical enrollment records without destructive deletions.
    """
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    student = db.execute(select(Student).where(Student.id == student_id, Student.school_id == school.id)).scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    active_enrollment = db.execute(
        select(StudentEnrollment).where(
            StudentEnrollment.student_id == student.id,
            StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE,
        )
    ).scalar_one_or_none()

    if active_enrollment:
        active_enrollment.enrollment_status = enrollment_status

    if enrollment_status in (EnrollmentStatus.WITHDRAWN, EnrollmentStatus.COMPLETED):
        student.is_active = False
    else:
        student.is_active = True

    db.commit()
    return {
        "student_id": str(student.id),
        "status": enrollment_status.value,
        "is_active": student.is_active,
        "notes": notes,
    }

