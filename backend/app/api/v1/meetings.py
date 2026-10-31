import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_school, PermissionChecker
from app.models.identity import User, School
from app.models.academic import ClassGroup, StudentEnrollment, Guardian, StudentGuardian, EnrollmentStatus
from app.models.meetings import SchoolMeeting, MeetingInvitation, MeetingResponse, MeetingResponseStatus
from app.models.communication import CommunicationCampaign, CampaignRecipient, TargetingMode, CampaignStatus, MessageDeliveryStatus
from app.schemas.meetings import MeetingCreateRequest, MeetingResponseSubmit
from app.utils.phone import calculate_sms_segments
from app.workers.campaign_tasks import dispatch_campaign_task

router = APIRouter()


@router.get("")
def list_meetings(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")
    meetings = db.execute(select(SchoolMeeting).where(SchoolMeeting.school_id == school.id).order_by(SchoolMeeting.meeting_date.desc())).scalars().all()
    results = []
    for m in meetings:
        inv_count = db.execute(select(func.count(MeetingInvitation.id)).where(MeetingInvitation.meeting_id == m.id)).scalar()
        confirmed_count = db.execute(
            select(func.count(MeetingResponse.id))
            .join(MeetingInvitation, MeetingInvitation.id == MeetingResponse.invitation_id)
            .where(MeetingInvitation.meeting_id == m.id, MeetingResponse.response_status == MeetingResponseStatus.CONFIRMED)
        ).scalar()
        declined_count = db.execute(
            select(func.count(MeetingResponse.id))
            .join(MeetingInvitation, MeetingInvitation.id == MeetingResponse.invitation_id)
            .where(MeetingInvitation.meeting_id == m.id, MeetingResponse.response_status == MeetingResponseStatus.DECLINED)
        ).scalar()

        results.append({
            "id": str(m.id),
            "title": m.title,
            "description": m.description,
            "meeting_date": str(m.meeting_date),
            "start_time": str(m.start_time),
            "end_time": str(m.end_time),
            "venue": m.venue,
            "invitations_count": inv_count,
            "confirmed_count": confirmed_count,
            "declined_count": declined_count,
        })
    return results


@router.post("")
def create_meeting(
    req: MeetingCreateRequest,
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("meeting:create")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    meeting = SchoolMeeting(
        school_id=school.id,
        created_by_user_id=current_user.id,
        title=req.title,
        description=req.description,
        meeting_date=req.meeting_date,
        start_time=req.start_time,
        end_time=req.end_time,
        venue=req.venue,
    )
    db.add(meeting)
    db.flush()

    # Resolve target guardians
    guardians_to_invite: List[Guardian] = []
    seen_guardians = set()

    if req.class_group_ids:
        for cid in req.class_group_ids:
            enrollments = db.execute(
                select(StudentEnrollment).where(
                    StudentEnrollment.class_group_id == cid,
                    StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE,
                )
            ).scalars().all()
            for en in enrollments:
                links = db.execute(select(StudentGuardian).where(StudentGuardian.student_id == en.student_id)).scalars().all()
                for gl in links:
                    g = gl.guardian
                    if g.id not in seen_guardians and g.primary_phone:
                        seen_guardians.add(g.id)
                        guardians_to_invite.append(g)

    if req.selected_guardian_ids:
        for gid in req.selected_guardian_ids:
            if gid not in seen_guardians:
                g = db.execute(select(Guardian).where(Guardian.id == gid, Guardian.school_id == school.id)).scalar_one_or_none()
                if g and g.primary_phone:
                    seen_guardians.add(g.id)
                    guardians_to_invite.append(g)

    # Create MeetingInvitations
    invitations = []
    for g in guardians_to_invite:
        inv = MeetingInvitation(
            meeting_id=meeting.id,
            guardian_id=g.id,
            phone_number=g.primary_phone,
            invitation_status="SENT",
        )
        db.add(inv)
        invitations.append(inv)

    # Send SMS invitations if enabled
    if req.send_sms_invitation and guardians_to_invite:
        sms_text = (
            f"Mkutano wa Wazazi: {meeting.title}. Tarehe: {meeting.meeting_date} kuanzia saa {meeting.start_time} "
            f"katika {meeting.venue}. Tafadhali thibitisha uwepo wako kupitia portal au *384*55#. {school.name}."
        )
        campaign = CommunicationCampaign(
            school_id=school.id,
            created_by_user_id=current_user.id,
            title=f"Mwaliko wa Mkutano: {meeting.title}",
            message_content=sms_text,
            targeting_mode=TargetingMode.SELECTED_GUARDIANS,
            status=CampaignStatus.PROCESSING,
            recipient_count=len(guardians_to_invite),
        )
        db.add(campaign)
        db.flush()

        for g in guardians_to_invite:
            segments, _ = calculate_sms_segments(sms_text)
            rec = CampaignRecipient(
                campaign_id=campaign.id,
                guardian_id=g.id,
                phone_number=g.primary_phone,
                personalized_text=sms_text,
                segments=segments,
                status=MessageDeliveryStatus.QUEUED,
            )
            db.add(rec)

        db.flush()
        dispatch_campaign_task.delay(str(campaign.id))

    db.commit()
    return {
        "status": "success",
        "meeting_id": str(meeting.id),
        "invitations_count": len(guardians_to_invite),
    }


@router.post("/respond")
def submit_meeting_response(
    req: MeetingResponseSubmit,
    db: Session = Depends(get_db),
):
    """
    Records guardian RSVP response to a meeting invitation (from portal, SMS, or USSD).
    """
    invitation = db.execute(select(MeetingInvitation).where(MeetingInvitation.id == req.invitation_id)).scalar_one_or_none()
    if not invitation:
        raise HTTPException(status_code=404, detail="Meeting invitation not found")

    existing_resp = db.execute(select(MeetingResponse).where(MeetingResponse.invitation_id == invitation.id)).scalar_one_or_none()
    if existing_resp:
        existing_resp.response_status = req.response_status
        existing_resp.comments = req.comments
        existing_resp.channel = req.channel
        existing_resp.responded_at = datetime.now(timezone.utc)
    else:
        resp = MeetingResponse(
            invitation_id=invitation.id,
            guardian_id=invitation.guardian_id,
            response_status=req.response_status,
            comments=req.comments,
            channel=req.channel,
        )
        db.add(resp)

    db.commit()
    return {"status": "success", "message": "Response recorded successfully"}
