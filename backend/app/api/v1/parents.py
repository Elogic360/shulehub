import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.identity import User
from app.models.academic import Guardian, StudentGuardian, Student, StudentEnrollment, EnrollmentStatus
from app.models.examinations import Examination, StudentExamResult, ResultStatus, ExaminationSubject
from app.models.fees import FeeInvoice, FeePayment, FeeStatus
from app.models.meetings import SchoolMeeting, MeetingInvitation, MeetingResponse
from app.models.communication import Announcement

router = APIRouter()


@router.get("/portal/summary")
def get_parent_portal_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Dedicated Parent Portal endpoint providing linked children, fee balances,
    published exam results, announcements, and meeting invitations.
    """
    guardian = db.execute(select(Guardian).where(Guardian.primary_phone == current_user.phone_number)).scalars().first()
    if not guardian:
        # Check by email
        if current_user.email:
            guardian = db.execute(select(Guardian).where(Guardian.email == current_user.email)).scalars().first()

    if not guardian:
        return {
            "is_guardian": False,
            "children": [],
            "announcements": [],
            "meetings": [],
            "message": "No student profile is currently linked to your phone number.",
        }

    # Linked children
    links = db.execute(select(StudentGuardian).where(StudentGuardian.guardian_id == guardian.id)).scalars().all()
    children_data = []

    for gl in links:
        student = gl.student
        en = db.execute(select(StudentEnrollment).where(StudentEnrollment.student_id == student.id, StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE)).scalars().first()
        class_name = en.class_group.name if en and en.class_group else "Unassigned"
        school = student.school

        # Latest published exam results
        results = db.execute(
            select(StudentExamResult)
            .join(ExaminationSubject, ExaminationSubject.id == StudentExamResult.examination_subject_id)
            .where(
                StudentExamResult.student_id == student.id,
                StudentExamResult.status == ResultStatus.PUBLISHED,
            )
        ).scalars().all()

        exam_scores = []
        for r in results:
            exam_scores.append({
                "subject": r.exam_subject.subject.name if r.exam_subject and r.exam_subject.subject else "",
                "score": float(r.score),
                "grade": r.grade,
                "remarks": r.remarks,
            })

        # Fee balance
        invoices = db.execute(
            select(FeeInvoice).where(
                FeeInvoice.student_id == student.id,
                FeeInvoice.status.in_([FeeStatus.UNPAID, FeeStatus.PARTIALLY_PAID, FeeStatus.OVERDUE]),
            )
        ).scalars().all()
        outstanding_fee = sum(float(inv.balance_due_tzs) for inv in invoices)

        children_data.append({
            "student_id": str(student.id),
            "admission_number": student.admission_number,
            "full_name": f"{student.first_name} {student.last_name}",
            "gender": student.gender.value,
            "school_name": school.name if school else "",
            "class_name": class_name,
            "relationship": gl.relationship_type.value,
            "outstanding_fee_tzs": outstanding_fee,
            "exam_results": exam_scores,
        })

    # School announcements
    announcements = db.execute(
        select(Announcement)
        .where(Announcement.school_id == guardian.school_id, Announcement.is_published == True)
        .order_by(Announcement.published_at.desc())
        .limit(5)
    ).scalars().all()

    ann_list = [{
        "id": str(a.id),
        "title": a.title,
        "content": a.content,
        "priority": a.priority,
        "published_at": a.published_at.isoformat() if a.published_at else "",
    } for a in announcements]

    # Meeting invitations
    invitations = db.execute(
        select(MeetingInvitation).where(MeetingInvitation.guardian_id == guardian.id).order_by(MeetingInvitation.created_at.desc())
    ).scalars().all()

    meet_list = []
    for inv in invitations:
        m = inv.meeting
        resp = db.execute(select(MeetingResponse).where(MeetingResponse.invitation_id == inv.id)).scalars().first()
        meet_list.append({
            "invitation_id": str(inv.id),
            "meeting_id": str(m.id),
            "title": m.title,
            "description": m.description,
            "meeting_date": str(m.meeting_date),
            "start_time": str(m.start_time),
            "venue": m.venue,
            "response_status": resp.response_status.value if resp else "PENDING",
        })

    return {
        "is_guardian": True,
        "guardian_name": guardian.full_name,
        "phone_number": guardian.primary_phone,
        "children": children_data,
        "announcements": ann_list,
        "meetings": meet_list,
    }
