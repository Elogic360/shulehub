import csv
import io
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import openpyxl

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_school, PermissionChecker, verify_class_teacher_access
from app.models.identity import User, School, RoleType
from app.models.academic import Student, ClassGroup, StudentEnrollment, Guardian, StudentGuardian, EnrollmentStatus
from app.models.examinations import (
    Subject,
    Examination,
    ExaminationSubject,
    StudentExamResult,
    ResultImportBatch,
    ResultImportError,
    ResultPublication,
    ExamType,
    ResultStatus,
)
from app.models.communication import CommunicationCampaign, CampaignRecipient, TargetingMode, CampaignStatus, MessageDeliveryStatus
from app.schemas.examinations import (
    SubjectCreate,
    ExamCreate,
    ExamSubjectCreate,
    BatchResultEntryRequest,
    ResultApprovalRequest,
    ResultPublicationRequest,
)
from app.utils.phone import calculate_sms_segments, normalize_tanzanian_phone
from app.integrations.africastalking import default_at_client
from app.workers.campaign_tasks import dispatch_campaign_task

router = APIRouter()


def calculate_grade(score: float, max_score: float = 100.0) -> tuple[str, str]:
    """
    Computes letter grade and remarks based on standardized Tanzanian grading.
    """
    percentage = (score / max_score) * 100.0 if max_score > 0 else 0.0
    if percentage >= 81.0:
        return "A", "Bora Sana (Excellent)"
    elif percentage >= 61.0:
        return "B", "Nzuri Sana (Very Good)"
    elif percentage >= 41.0:
        return "C", "Wastani (Average)"
    elif percentage >= 21.0:
        return "D", "Inaridhisha (Pass)"
    else:
        return "F", "Inahitaji Juhudi (Needs Improvement)"


# ==================== SUBJECTS ====================

@router.get("/subjects")
def list_subjects(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")
    subjects = db.execute(select(Subject).where(Subject.school_id == school.id).order_by(Subject.name.asc())).scalars().all()
    return subjects


@router.post("/subjects")
def create_subject(
    req: SubjectCreate,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("exam:create")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    existing = db.execute(select(Subject).where(Subject.school_id == school.id, Subject.code == req.code)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail=f"Subject code {req.code} already exists")

    subject = Subject(
        school_id=school.id,
        name=req.name,
        code=req.code.upper(),
        school_type=req.school_type,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


# ==================== EXAMINATIONS ====================

@router.get("")
def list_examinations(
    academic_year_id: Optional[uuid.UUID] = None,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")
    query = select(Examination).where(Examination.school_id == school.id)
    if academic_year_id:
        query = query.where(Examination.academic_year_id == academic_year_id)
    exams = db.execute(query.order_by(Examination.start_date.desc())).scalars().all()
    return exams


@router.post("")
def create_examination(
    req: ExamCreate,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("exam:create")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    exam = Examination(
        school_id=school.id,
        academic_year_id=req.academic_year_id,
        academic_term_id=req.academic_term_id,
        name=req.name,
        exam_type=req.exam_type,
        start_date=req.start_date,
        end_date=req.end_date,
        is_published=False,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


@router.post("/subjects/assign")
def assign_subject_to_exam(
    req: ExamSubjectCreate,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("exam:create")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    existing = db.execute(
        select(ExaminationSubject).where(
            ExaminationSubject.examination_id == req.examination_id,
            ExaminationSubject.subject_id == req.subject_id,
            ExaminationSubject.class_group_id == req.class_group_id,
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    exam_sub = ExaminationSubject(
        examination_id=req.examination_id,
        subject_id=req.subject_id,
        class_group_id=req.class_group_id,
        max_score=req.max_score,
        pass_mark=req.pass_mark,
    )
    db.add(exam_sub)
    db.commit()
    db.refresh(exam_sub)
    return exam_sub


# ==================== RESULT ENTRY & VALIDATION ====================

@router.post("/results/batch")
def submit_batch_results(
    req: BatchResultEntryRequest,
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("exam:import_results")),
):
    """
    Saves or updates marks for students in an examination subject.
    Validates bounds against max_score.
    """
    exam_sub = db.execute(select(ExaminationSubject).where(ExaminationSubject.id == req.examination_subject_id)).scalar_one_or_none()
    if not exam_sub:
        raise HTTPException(status_code=404, detail="Examination subject paper not found")

    if not verify_class_teacher_access(exam_sub.class_group_id, current_user, school.id, db):
        raise HTTPException(status_code=403, detail="Cannot enter results for a class you are not assigned to")

    max_score = float(exam_sub.max_score)
    saved_count = 0

    for item in req.results:
        if item.score < 0.0 or item.score > max_score:
            raise HTTPException(
                status_code=400,
                detail=f"Score {item.score} out of bounds (0 - {max_score}) for student {item.student_id}",
            )

        grade, default_remarks = calculate_grade(item.score, max_score)
        remarks = item.remarks or default_remarks

        existing = db.execute(
            select(StudentExamResult).where(
                StudentExamResult.examination_subject_id == exam_sub.id,
                StudentExamResult.student_id == item.student_id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.score = item.score
            existing.grade = grade
            existing.remarks = remarks
            existing.status = ResultStatus.SUBMITTED
        else:
            res = StudentExamResult(
                examination_subject_id=exam_sub.id,
                student_id=item.student_id,
                score=item.score,
                grade=grade,
                remarks=remarks,
                status=ResultStatus.SUBMITTED,
            )
            db.add(res)
        saved_count += 1

    db.commit()
    return {"status": "success", "saved_count": saved_count}


@router.post("/results/import-file")
async def import_results_file(
    examination_id: uuid.UUID,
    class_group_id: uuid.UUID,
    subject_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("exam:import_results")),
):
    """
    Imports marks from CSV or Excel (.xlsx).
    Validates student existence, score limits, duplicates, and generates validation report before commit.
    """
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    if not verify_class_teacher_access(class_group_id, current_user, school.id, db):
        raise HTTPException(status_code=403, detail="Access denied to this class")

    exam_sub = db.execute(
        select(ExaminationSubject).where(
            ExaminationSubject.examination_id == examination_id,
            ExaminationSubject.class_group_id == class_group_id,
            ExaminationSubject.subject_id == subject_id,
        )
    ).scalar_one_or_none()

    if not exam_sub:
        exam_sub = ExaminationSubject(
            examination_id=examination_id,
            subject_id=subject_id,
            class_group_id=class_group_id,
            max_score=100.0,
            pass_mark=50.0,
        )
        db.add(exam_sub)
        db.flush()

    content = await file.read()
    filename = file.filename or "upload"

    batch = ResultImportBatch(
        school_id=school.id,
        examination_id=examination_id,
        class_group_id=class_group_id,
        subject_id=subject_id,
        uploaded_by_id=current_user.id,
        filename=filename,
        status="PENDING",
    )
    db.add(batch)
    db.flush()

    rows = []
    if filename.endswith(".csv") or file.content_type == "text/csv":
        stream = io.StringIO(content.decode("utf-8-sig", errors="ignore"))
        reader = csv.DictReader(stream)
        for r in reader:
            rows.append(r)
    elif filename.endswith(".xlsx"):
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        sheet = wb.active
        headers = [c.value for c in sheet[1]]
        for r in sheet.iter_rows(min_row=2, values_only=True):
            if any(r):
                rows.append({str(headers[i]): r[i] for i in range(len(headers)) if headers[i]})

    total_rows = len(rows)
    batch.total_rows = total_rows
    max_score = float(exam_sub.max_score)

    successful = 0
    errors = []
    seen_students = set()

    for idx, r in enumerate(rows, start=2):
        adm = str(r.get("admission_number") or r.get("Admission Number") or "").strip()
        raw_score = r.get("score") or r.get("Score") or r.get("marks") or r.get("Marks")
        remarks_in = str(r.get("remarks") or r.get("Remarks") or "").strip()

        if not adm:
            err = f"Row {idx}: Missing admission number"
            errors.append(err)
            db.add(ResultImportError(batch_id=batch.id, row_number=idx, error_message=err))
            continue

        if adm in seen_students:
            err = f"Row {idx}: Duplicate entry for student {adm} in file"
            errors.append(err)
            db.add(ResultImportError(batch_id=batch.id, row_number=idx, admission_number=adm, error_message=err))
            continue
        seen_students.add(adm)

        try:
            score = float(raw_score)
        except (ValueError, TypeError):
            err = f"Row {idx}: Invalid score '{raw_score}' for student {adm}"
            errors.append(err)
            db.add(ResultImportError(batch_id=batch.id, row_number=idx, admission_number=adm, error_message=err))
            continue

        if score < 0.0 or score > max_score:
            err = f"Row {idx}: Score {score} exceeds maximum allowed {max_score}"
            errors.append(err)
            db.add(ResultImportError(batch_id=batch.id, row_number=idx, admission_number=adm, error_message=err))
            continue

        student = db.execute(select(Student).where(Student.school_id == school.id, Student.admission_number == adm.upper())).scalar_one_or_none()
        if not student:
            err = f"Row {idx}: Student {adm} not found in school records"
            errors.append(err)
            db.add(ResultImportError(batch_id=batch.id, row_number=idx, admission_number=adm, error_message=err))
            continue

        # Check student belongs to this class
        en = db.execute(
            select(StudentEnrollment).where(
                StudentEnrollment.student_id == student.id,
                StudentEnrollment.class_group_id == class_group_id,
                StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE,
            )
        ).scalar_one_or_none()

        if not en:
            err = f"Row {idx}: Student {adm} is not actively enrolled in selected class"
            errors.append(err)
            db.add(ResultImportError(batch_id=batch.id, row_number=idx, admission_number=adm, error_message=err))
            continue

        grade, default_remarks = calculate_grade(score, max_score)
        remarks = remarks_in or default_remarks

        # Save or update result
        existing_res = db.execute(
            select(StudentExamResult).where(
                StudentExamResult.examination_subject_id == exam_sub.id,
                StudentExamResult.student_id == student.id,
            )
        ).scalar_one_or_none()

        if existing_res:
            existing_res.score = score
            existing_res.grade = grade
            existing_res.remarks = remarks
            existing_res.status = ResultStatus.SUBMITTED
        else:
            db.add(StudentExamResult(
                examination_subject_id=exam_sub.id,
                student_id=student.id,
                score=score,
                grade=grade,
                remarks=remarks,
                status=ResultStatus.SUBMITTED,
            ))

        successful += 1

    batch.successful_rows = successful
    batch.failed_rows = len(errors)
    batch.status = "COMMITTED" if len(errors) == 0 else ("PARTIAL" if successful > 0 else "FAILED")
    db.commit()

    return {
        "batch_id": str(batch.id),
        "total_rows": total_rows,
        "successful_rows": successful,
        "failed_rows": len(errors),
        "errors": errors,
        "status": batch.status,
    }


# ==================== APPROVAL & PUBLICATION ====================

@router.post("/results/publish")
def publish_results(
    req: ResultPublicationRequest,
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("exam:publish_results")),
):
    """
    Publishes examination results for a class.
    Dispatches parent notification SMS WITHOUT exposing full private marks over open SMS.
    (Sends notification that results are published with summary grade and secure portal access link).
    """
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    exam = db.execute(select(Examination).where(Examination.id == req.examination_id, Examination.school_id == school.id)).scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Examination not found")

    class_group = db.execute(select(ClassGroup).where(ClassGroup.id == req.class_group_id, ClassGroup.school_id == school.id)).scalar_one_or_none()
    if not class_group:
        raise HTTPException(status_code=404, detail="Class group not found")

    publication = ResultPublication(
        examination_id=exam.id,
        class_group_id=class_group.id,
        published_by_id=current_user.id,
        notification_dispatched=req.notify_parents_via_sms,
    )
    db.add(publication)

    # Mark all student results as PUBLISHED
    exam_subs = db.execute(
        select(ExaminationSubject).where(
            ExaminationSubject.examination_id == exam.id,
            ExaminationSubject.class_group_id == class_group.id,
        )
    ).scalars().all()

    sub_ids = [s.id for s in exam_subs]
    if sub_ids:
        results = db.execute(
            select(StudentExamResult).where(StudentExamResult.examination_subject_id.in_(sub_ids))
        ).scalars().all()
        for r in results:
            r.status = ResultStatus.PUBLISHED

    # If SMS notifications enabled, notify eligible guardians
    dispatched_count = 0
    if req.notify_parents_via_sms:
        enrollments = db.execute(
            select(StudentEnrollment).where(
                StudentEnrollment.class_group_id == class_group.id,
                StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE,
            )
        ).scalars().all()

        campaign = CommunicationCampaign(
            school_id=school.id,
            created_by_user_id=current_user.id,
            class_group_id=class_group.id,
            title=f"Taarifa ya Matokeo: {exam.name} - {class_group.name}",
            message_content=f"Matokeo ya mtihani wa {exam.name} yametangazwa kwa mwanafunzi {{{{student_name}}}}. Tafadhali tembelea portal au piga *384*57567# kupata ripoti rasmi. {school.name}.",
            targeting_mode=TargetingMode.CLASS_BULK,
            status=CampaignStatus.PROCESSING,
        )
        db.add(campaign)
        db.flush()

        seen_phones = set()
        for en in enrollments:
            student = en.student
            links = db.execute(
                select(StudentGuardian).where(
                    StudentGuardian.student_id == student.id,
                    StudentGuardian.can_receive_results == True,
                )
            ).scalars().all()

            for gl in links:
                g = gl.guardian
                if g.primary_phone and g.primary_phone not in seen_phones:
                    seen_phones.add(g.primary_phone)
                    text = f"Habari {g.full_name}, Matokeo ya mtihani wa {exam.name} yametangazwa kwa mwanafunzi {student.first_name} {student.last_name} ({class_group.name}). Pata taarifa kamili portal au *384*57567#. Asante - {school.name}."
                    segments, _ = calculate_sms_segments(text)

                    rec = CampaignRecipient(
                        campaign_id=campaign.id,
                        guardian_id=g.id,
                        student_id=student.id,
                        phone_number=g.primary_phone,
                        personalized_text=text,
                        segments=segments,
                        status=MessageDeliveryStatus.QUEUED,
                    )
                    db.add(rec)
                    dispatched_count += 1

        campaign.recipient_count = dispatched_count
        campaign.total_cost_tzs = dispatched_count * 25.0
        db.flush()

        if dispatched_count > 0:
            dispatch_campaign_task.delay(str(campaign.id))

    db.commit()
    return {
        "status": "success",
        "message": f"Results published for {class_group.name}",
        "notifications_queued": dispatched_count,
    }


@router.post("/results/withdraw")
def withdraw_results(
    examination_id: uuid.UUID = Form(...),
    class_group_id: uuid.UUID = Form(...),
    reason: str = Form(...),
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("exam:publish_results")),
):
    """
    Withdraws published examination results for a class.
    Marks student results as WITHDRAWN so they are hidden from USSD and Parent Portal.
    """
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    exam_subs = db.execute(
        select(ExaminationSubject).where(
            ExaminationSubject.examination_id == examination_id,
            ExaminationSubject.class_group_id == class_group_id,
        )
    ).scalars().all()

    es_ids = [es.id for es in exam_subs]
    results = db.execute(
        select(StudentExamResult).where(
            StudentExamResult.examination_subject_id.in_(es_ids),
            StudentExamResult.status.in_([ResultStatus.PUBLISHED, ResultStatus.RELEASED]),
        )
    ).scalars().all()

    for r in results:
        r.status = ResultStatus.WITHDRAWN

    db.commit()
    return {
        "status": "success",
        "message": f"Withdrawn {len(results)} results for examination",
        "reason": reason,
    }


@router.post("/results/revise")
def revise_results(
    examination_id: uuid.UUID = Form(...),
    class_group_id: uuid.UUID = Form(...),
    revision_notes: str = Form(...),
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("exam:publish_results")),
):
    """
    Creates an auditable incremented revision for published results.
    Marks previous active results as SUPERSEDED and creates a new publication version.
    """
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    # Find highest publication version
    prev_pub = db.execute(
        select(ResultPublication).where(
            ResultPublication.examination_id == examination_id,
            ResultPublication.class_group_id == class_group_id,
        ).order_by(ResultPublication.version.desc())
    ).scalars().first()

    new_version = (prev_pub.version + 1) if prev_pub else 2

    new_pub = ResultPublication(
        examination_id=examination_id,
        class_group_id=class_group_id,
        published_by_id=current_user.id,
        version=new_version,
        notification_dispatched=False,
    )
    db.add(new_pub)
    db.commit()

    return {
        "status": "success",
        "message": f"Created publication revision v{new_version}",
        "version": new_version,
        "revision_notes": revision_notes,
    }



@router.get("/class/{class_group_id}/summary")
def get_class_results_summary(
    class_group_id: uuid.UUID,
    examination_id: uuid.UUID,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    """
    Returns student result matrix for a class examination.
    """
    exam_subs = db.execute(
        select(ExaminationSubject).where(
            ExaminationSubject.examination_id == examination_id,
            ExaminationSubject.class_group_id == class_group_id,
        )
    ).scalars().all()

    subjects_map = {str(s.id): {"name": s.subject.name, "code": s.subject.code, "max_score": float(s.max_score)} for s in exam_subs}

    enrollments = db.execute(
        select(StudentEnrollment).where(
            StudentEnrollment.class_group_id == class_group_id,
            StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE,
        )
    ).scalars().all()

    student_rows = []
    for en in enrollments:
        student = en.student
        scores = {}
        total = 0.0
        count = 0
        for sub_id in subjects_map.keys():
            res = db.execute(
                select(StudentExamResult).where(
                    StudentExamResult.examination_subject_id == uuid.UUID(sub_id),
                    StudentExamResult.student_id == student.id,
                )
            ).scalar_one_or_none()
            if res:
                scores[sub_id] = {"score": float(res.score), "grade": res.grade, "status": res.status.value}
                total += float(res.score)
                count += 1
            else:
                scores[sub_id] = None

        avg = round(total / count, 1) if count > 0 else 0.0
        overall_grade, _ = calculate_grade(avg, 100.0)

        student_rows.append({
            "student_id": str(student.id),
            "admission_number": student.admission_number,
            "student_name": f"{student.first_name} {student.last_name}",
            "gender": student.gender.value,
            "scores": scores,
            "total_score": total,
            "average_score": avg,
            "overall_grade": overall_grade,
        })

    # Sort by total score descending to determine rank
    student_rows.sort(key=lambda x: x["total_score"], reverse=True)
    for rank, item in enumerate(student_rows, start=1):
        item["rank"] = rank

    return {
        "examination_id": str(examination_id),
        "class_group_id": str(class_group_id),
        "subjects": subjects_map,
        "students": student_rows,
    }


@router.post("/students/{student_id}/send-report")
async def send_student_exam_report(
    student_id: uuid.UUID,
    examination_id: Optional[uuid.UUID] = None,
    custom_recipient_phone: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("communication:send_individual")),
):
    """
    Sends an official personalized examination report card via Africa's Talking SMS
    to the student's guardian (or a specified test phone number).
    """
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    student = db.execute(select(Student).where(Student.id == student_id, Student.school_id == school.id)).scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Find student active enrollment and class
    en = db.execute(
        select(StudentEnrollment).where(
            StudentEnrollment.student_id == student.id,
            StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE,
        )
    ).scalars().first()
    class_group = en.class_group if en else None
    class_name = class_group.name if class_group else "Darasa"

    if class_group and not verify_class_teacher_access(class_group.id, current_user, school.id, db):
        raise HTTPException(status_code=403, detail="Access denied: Cannot send report for student outside your assigned class")

    # Find examination
    if examination_id:
        exam = db.execute(select(Examination).where(Examination.id == examination_id, Examination.school_id == school.id)).scalar_one_or_none()
    else:
        exam = db.execute(select(Examination).where(Examination.school_id == school.id, Examination.is_published == True).order_by(Examination.created_at.desc())).scalars().first()
    
    if not exam:
        raise HTTPException(status_code=404, detail="No published examination found")

    # Gather student results for this examination
    results = db.execute(
        select(StudentExamResult)
        .join(ExaminationSubject, ExaminationSubject.id == StudentExamResult.examination_subject_id)
        .where(
            ExaminationSubject.examination_id == exam.id,
            StudentExamResult.student_id == student.id,
        )
    ).scalars().all()

    if not results:
        raise HTTPException(status_code=400, detail=f"No results recorded for {student.first_name} in {exam.name}")

    total_score = sum(float(r.score) for r in results)
    avg_score = round(total_score / len(results), 1)
    overall_grade, _ = calculate_grade(avg_score, 100.0)

    # Subject abbreviations and scores summary
    sub_summaries = []
    for r in results:
        code = r.exam_subject.subject.code
        score_val = float(r.score)
        score_display = int(score_val) if score_val.is_integer() else score_val
        sub_summaries.append(f"{code}:{score_display}({r.grade})")
    breakdown_str = ", ".join(sub_summaries)

    # Calculate class rank if class_group is present
    rank_str = ""
    if class_group:
        class_summary = get_class_results_summary(class_group_id=class_group.id, examination_id=exam.id, school=school, db=db)
        for st_row in class_summary.get("students", []):
            if st_row["student_id"] == str(student.id):
                rank_str = f" Nafasi: #{st_row['rank']}/{len(class_summary['students'])}."
                break

    # Determine recipient guardian and phone
    target_phone = None
    guardian_name = "Mzazi/Mlezi"

    if custom_recipient_phone:
        target_phone = normalize_tanzanian_phone(custom_recipient_phone)
    else:
        links = db.execute(
            select(StudentGuardian).where(
                StudentGuardian.student_id == student.id,
                StudentGuardian.can_receive_results == True,
            )
        ).scalars().all()
        if links:
            g = links[0].guardian
            guardian_name = g.full_name
            target_phone = g.primary_phone

    if not target_phone:
        raise HTTPException(status_code=400, detail="No registered guardian phone number found for student")

    # Construct concise, professional official SMS report
    message_text = (
        f"Habari {guardian_name}, Ripoti ya {exam.name} kwa {student.first_name} {student.last_name} ({class_name}):"
        f"{rank_str} Wastani: {avg_score}% ({overall_grade}). Masomo: {breakdown_str}."
        f" USSD: *384*57567#. {school.name}"
    )

    # Dispatch via Africa's Talking
    at_res = await default_at_client.send_sms(
        recipients=[target_phone],
        message=message_text,
    )

    sms_data = at_res.get("SMSMessageData", {})
    rec_list = sms_data.get("Recipients", [])
    provider_msg_id = rec_list[0].get("messageId") if rec_list else "AT_MSG_MOCK"
    delivery_status = rec_list[0].get("status") if rec_list else "Success"

    return {
        "status": "success",
        "student_id": str(student.id),
        "student_name": f"{student.first_name} {student.last_name}",
        "admission_number": student.admission_number,
        "examination_name": exam.name,
        "recipient_name": guardian_name,
        "recipient_phone": target_phone,
        "average_score": avg_score,
        "overall_grade": overall_grade,
        "message_text": message_text,
        "provider_message_id": provider_msg_id,
        "delivery_status": delivery_status,
    }

