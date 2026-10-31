import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_school, PermissionChecker
from app.models.identity import User, School
from app.models.academic import Student, Guardian, StudentGuardian
from app.models.necta import (
    NectaExamination,
    NectaCandidate,
    NectaCandidateSubject,
    NectaStudentMatch,
    NectaExamType,
    NectaMatchStatus,
)
from app.models.communication import CommunicationCampaign, CampaignRecipient, MessageDeliveryStatus, TargetingMode
from app.services.necta_service import NectaResultParser, NectaMatcher
from app.integrations.africastalking import AfricasTalkingClient

router = APIRouter()


@router.get("/examinations")
def list_necta_examinations(
    db: Session = Depends(get_db),
    school: School = Depends(get_current_school),
):
    """Lists external NECTA national assessments registered for the school."""
    exams = db.execute(
        select(NectaExamination).where(
            (NectaExamination.school_id == school.id) | (NectaExamination.school_id == None)
        ).order_by(desc(NectaExamination.exam_year))
    ).scalars().all()

    return [
        {
            "id": str(e.id),
            "exam_year": e.exam_year,
            "exam_type": e.exam_type.value,
            "center_number": e.center_number,
            "center_name": e.center_name,
            "source_url": e.source_url,
            "is_published": e.is_published,
            "total_candidates": len(e.candidates),
        }
        for e in exams
    ]


@router.post("/examinations", status_code=status.HTTP_201_CREATED)
def create_necta_examination(
    exam_year: int = Form(...),
    exam_type: NectaExamType = Form(...),
    center_number: str = Form(...),
    center_name: str = Form(...),
    source_url: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    _: bool = Depends(PermissionChecker("exam:manage")),
):
    """Registers a new NECTA examination assessment center."""
    existing = db.execute(
        select(NectaExamination).where(
            NectaExamination.exam_year == exam_year,
            NectaExamination.exam_type == exam_type,
            NectaExamination.center_number == center_number.upper(),
        )
    ).scalar_one_or_none()

    if existing:
        return existing

    exam = NectaExamination(
        school_id=school.id,
        exam_year=exam_year,
        exam_type=exam_type,
        center_number=center_number.upper(),
        center_name=center_name,
        source_url=source_url,
        source_provenance={
            "registered_by": current_user.email,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        },
        is_published=True,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


@router.post("/examinations/{exam_id}/ingest")
def ingest_necta_candidate_data(
    exam_id: uuid.UUID,
    raw_lines: List[str],
    db: Session = Depends(get_db),
    school: School = Depends(get_current_school),
    _: bool = Depends(PermissionChecker("exam:manage")),
):
    """
    Ingests candidate results lines parsed from structured NECTA result sets.
    Validates index numbers and subject grades.
    """
    exam = db.execute(select(NectaExamination).where(NectaExamination.id == exam_id)).scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="NECTA examination not found")

    ingested_count = 0
    parser = NectaResultParser()

    for line in raw_lines:
        parsed = parser.parse_candidate_row(line)
        if not parsed:
            continue

        cand = db.execute(
            select(NectaCandidate).where(
                NectaCandidate.examination_id == exam.id,
                NectaCandidate.index_number == parsed["index_number"],
            )
        ).scalar_one_or_none()

        if not cand:
            cand = NectaCandidate(
                examination_id=exam.id,
                index_number=parsed["index_number"],
                candidate_name=parsed["candidate_name"],
                sex=parsed["sex"],
                division=parsed["division"],
                points=parsed["points"],
            )
            db.add(cand)
            db.flush()

            for s in parsed["subjects"]:
                db.add(NectaCandidateSubject(
                    candidate_id=cand.id,
                    subject_code=s["code"],
                    subject_name=s["name"],
                    grade=s["grade"],
                ))
            ingested_count += 1

    db.commit()
    return {"status": "success", "ingested_candidates": ingested_count}


@router.post("/auto-match")
def auto_match_candidates(
    examination_id: uuid.UUID = Form(...),
    db: Session = Depends(get_db),
    school: School = Depends(get_current_school),
    _: bool = Depends(PermissionChecker("exam:manage")),
):
    """Runs automated index number and name matching against enrolled school students."""
    matcher = NectaMatcher(db, school.id)
    return matcher.match_candidates(examination_id)


@router.get("/matches")
def list_student_matches(
    examination_id: Optional[uuid.UUID] = None,
    match_status: Optional[NectaMatchStatus] = None,
    db: Session = Depends(get_db),
    school: School = Depends(get_current_school),
):
    """Lists student matching review candidates for approval or rejection."""
    query = select(NectaStudentMatch).where(NectaStudentMatch.school_id == school.id)
    if match_status:
        query = query.where(NectaStudentMatch.status == match_status)
    if examination_id:
        query = query.join(NectaCandidate, NectaCandidate.id == NectaStudentMatch.candidate_id).where(
            NectaCandidate.examination_id == examination_id
        )

    matches = db.execute(query.order_by(NectaStudentMatch.match_confidence.desc())).scalars().all()
    results = []
    for m in matches:
        cand = m.candidate
        student = m.student
        results.append({
            "match_id": str(m.id),
            "status": m.status.value,
            "match_confidence": float(m.match_confidence),
            "review_notes": m.review_notes,
            "candidate": {
                "id": str(cand.id),
                "index_number": cand.index_number,
                "candidate_name": cand.candidate_name,
                "sex": cand.sex,
                "division": cand.division,
                "points": cand.points,
            },
            "student": {
                "id": str(student.id),
                "admission_number": student.admission_number,
                "full_name": f"{student.first_name} {student.last_name}",
            },
        })
    return results


@router.post("/matches/{match_id}/review")
def review_student_match(
    match_id: uuid.UUID,
    decision: NectaMatchStatus = Form(...),  # MATCHED or REJECTED
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("exam:manage")),
):
    """Approves or rejects a proposed student NECTA match."""
    match = db.execute(
        select(NectaStudentMatch).where(NectaStudentMatch.id == match_id, NectaStudentMatch.school_id == school.id)
    ).scalar_one_or_none()

    if not match:
        raise HTTPException(status_code=404, detail="Match record not found")

    match.status = decision
    match.reviewed_by_id = current_user.id
    match.reviewed_at = datetime.now(timezone.utc)
    match.review_notes = notes or f"Reviewed and set to {decision.value}"
    db.commit()

    return {"status": "success", "match_id": str(match.id), "decision": decision.value}


@router.post("/matches/{match_id}/notify")
def notify_guardian_necta_result(
    match_id: uuid.UUID,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("exam:publish_results")),
):
    """
    Sends a confidential SMS notification to the verified guardian that their child's
    NECTA national assessment results have been matched and verified.
    Does NOT disclose division or private marks in open SMS.
    """
    match = db.execute(
        select(NectaStudentMatch).where(
            NectaStudentMatch.id == match_id,
            NectaStudentMatch.school_id == school.id,
            NectaStudentMatch.status == NectaMatchStatus.MATCHED,
        )
    ).scalar_one_or_none()

    if not match:
        raise HTTPException(status_code=400, detail="Cannot notify for an unverified/unmatched candidate")

    student = match.student
    cand = match.candidate
    exam = cand.examination

    guardian_links = db.execute(
        select(StudentGuardian).where(StudentGuardian.student_id == student.id, StudentGuardian.can_receive_results == True)
    ).scalars().all()

    notified = 0
    at_client = AfricasTalkingClient()

    for gl in guardian_links:
        g = gl.guardian
        if g.primary_phone:
            text = (
                f"Habari {g.full_name}, Matokeo rasmi ya NECTA {exam.exam_type.value} {exam.exam_year} "
                f"kwa {student.first_name} {student.last_name} yamethibitishwa. "
                f"Piga *384*55# au tembelea portal ya shule kuona ripoti. - {school.name}"
            )
            import asyncio
            asyncio.create_task(at_client.send_sms(recipients=[g.primary_phone], message=text))
            notified += 1

    return {"status": "success", "guardians_notified": notified}
