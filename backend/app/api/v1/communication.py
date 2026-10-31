import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_school, PermissionChecker, verify_class_teacher_access
from app.models.identity import User, School, RoleType
from app.models.academic import (
    ClassGroup,
    Student,
    StudentEnrollment,
    Guardian,
    StudentGuardian,
    EnrollmentStatus,
)
from app.models.communication import (
    CommunicationCampaign,
    CampaignRecipient,
    MessageTemplate,
    TargetingMode,
    CampaignStatus,
    MessageDeliveryStatus,
    MessageCostRecord,
)
from app.models.operations import OutboxEvent
from app.schemas.communication import CampaignCreateRequest, MessageTemplateCreate
from app.utils.phone import calculate_sms_segments
from app.workers.campaign_tasks import dispatch_campaign_task

router = APIRouter()


def render_message_template(
    template_str: str,
    context: Dict[str, Any],
) -> str:
    """Replaces personalized variables in template safely."""
    rendered = template_str
    for k, v in context.items():
        rendered = rendered.replace(f"{{{{{k}}}}}", str(v))
    return rendered


@router.post("/preview")
def preview_campaign(
    req: CampaignCreateRequest,
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    """
    Simulates recipient resolution, variable substitution, deduplication,
    SMS segmentation, and cost estimation prior to dispatch.
    """
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    recipients_data = resolve_recipients(req, school, db)
    
    total_segments = 0
    preview_items = []
    seen_phones = set()

    for item in recipients_data:
        phone = item["phone"]
        if phone in seen_phones:
            continue
        seen_phones.add(phone)

        context = {
            "parent_name": item["guardian_name"],
            "student_name": item["student_name"],
            "class_name": item["class_name"],
            "school_name": school.name,
            "meeting_date": item.get("meeting_date", "Itaarifiwa"),
            "meeting_time": item.get("meeting_time", ""),
            "exam_name": item.get("exam_name", ""),
            "fee_balance": item.get("fee_balance", "0"),
            "due_date": item.get("due_date", ""),
        }
        personalized = render_message_template(req.message_content, context)
        segments, is_unicode = calculate_sms_segments(personalized)
        total_segments += segments

        preview_items.append({
            "guardian_name": item["guardian_name"],
            "student_name": item["student_name"],
            "phone_number": phone,
            "rendered_text": personalized,
            "segments": segments,
            "is_unicode": is_unicode,
            "estimated_cost_tzs": segments * 25.0,
        })

    estimated_total_cost = total_segments * 25.0

    return {
        "unique_recipients_count": len(preview_items),
        "total_segments": total_segments,
        "estimated_total_cost_tzs": estimated_total_cost,
        "preview_sample": preview_items[:10],
    }


def resolve_recipients(req: CampaignCreateRequest, school: School, db: Session) -> List[Dict[str, Any]]:
    recipients = []

    if req.targeting_mode == TargetingMode.CLASS_BULK:
        if not req.class_group_id:
            raise HTTPException(status_code=400, detail="class_group_id required for CLASS_BULK mode")
        
        class_grp = db.execute(select(ClassGroup).where(ClassGroup.id == req.class_group_id)).scalar_one_or_none()
        class_name = class_grp.name if class_grp else ""

        enrollments = db.execute(
            select(StudentEnrollment)
            .where(
                StudentEnrollment.class_group_id == req.class_group_id,
                StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE,
            )
        ).scalars().all()

        for en in enrollments:
            student = en.student
            guardians_links = db.execute(
                select(StudentGuardian).where(StudentGuardian.student_id == student.id)
            ).scalars().all()

            for gl in guardians_links:
                g = gl.guardian
                if g.primary_phone:
                    recipients.append({
                        "guardian_id": g.id,
                        "guardian_name": g.full_name,
                        "student_id": student.id,
                        "student_name": f"{student.first_name} {student.last_name}",
                        "class_name": class_name,
                        "phone": g.primary_phone,
                    })

    elif req.targeting_mode == TargetingMode.SELECTED_GUARDIANS:
        if not req.guardian_ids:
            raise HTTPException(status_code=400, detail="guardian_ids required for SELECTED_GUARDIANS mode")
        
        for g_id in req.guardian_ids:
            guardian = db.execute(select(Guardian).where(Guardian.id == g_id, Guardian.school_id == school.id)).scalar_one_or_none()
            if guardian and guardian.primary_phone:
                # Find linked student if any
                link = db.execute(select(StudentGuardian).where(StudentGuardian.guardian_id == guardian.id)).scalars().first()
                st_name = ""
                cl_name = ""
                st_id = None
                if link:
                    st = link.student
                    st_id = st.id
                    st_name = f"{st.first_name} {st.last_name}"
                    en = db.execute(select(StudentEnrollment).where(StudentEnrollment.student_id == st.id, StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE)).scalars().first()
                    if en and en.class_group:
                        cl_name = en.class_group.name

                recipients.append({
                    "guardian_id": guardian.id,
                    "guardian_name": guardian.full_name,
                    "student_id": st_id,
                    "student_name": st_name,
                    "class_name": cl_name,
                    "phone": guardian.primary_phone,
                })

    elif req.targeting_mode == TargetingMode.INDIVIDUAL:
        # Teacher sends to one guardian
        g_id = req.guardian_ids[0] if req.guardian_ids else None
        if not g_id:
            raise HTTPException(status_code=400, detail="At least one guardian required for INDIVIDUAL mode")
        guardian = db.execute(select(Guardian).where(Guardian.id == g_id, Guardian.school_id == school.id)).scalar_one_or_none()
        if not guardian or not guardian.primary_phone:
            raise HTTPException(status_code=404, detail="Guardian not found or missing phone")

        st_name = ""
        cl_name = ""
        st_id = req.student_id
        if req.student_id:
            st = db.execute(select(Student).where(Student.id == req.student_id)).scalar_one_or_none()
            if st:
                st_name = f"{st.first_name} {st.last_name}"
                en = db.execute(select(StudentEnrollment).where(StudentEnrollment.student_id == st.id, StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE)).scalars().first()
                if en and en.class_group:
                    cl_name = en.class_group.name

        recipients.append({
            "guardian_id": guardian.id,
            "guardian_name": guardian.full_name,
            "student_id": st_id,
            "student_name": st_name,
            "class_name": cl_name,
            "phone": guardian.primary_phone,
        })

    return recipients


@router.post("")
def create_and_dispatch_campaign(
    req: CampaignCreateRequest,
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("communication:send_bulk")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    if req.class_group_id and not verify_class_teacher_access(req.class_group_id, current_user, school.id, db):
        raise HTTPException(status_code=403, detail="Cannot send announcements to a class you are not assigned to")

    resolved = resolve_recipients(req, school, db)
    if not resolved:
        raise HTTPException(status_code=400, detail="No eligible guardian recipients found for this selection")

    campaign = CommunicationCampaign(
        school_id=school.id,
        created_by_user_id=current_user.id,
        class_group_id=req.class_group_id,
        title=req.title,
        message_content=req.message_content,
        targeting_mode=req.targeting_mode,
        status=CampaignStatus.SCHEDULED if req.scheduled_at else CampaignStatus.PROCESSING,
        scheduled_at=req.scheduled_at,
        recipient_count=len(resolved),
    )
    db.add(campaign)
    db.flush()

    seen_phones = set()
    total_cost = 0.0

    for item in resolved:
        phone = item["phone"]
        if phone in seen_phones:
            continue
        seen_phones.add(phone)

        context = {
            "parent_name": item["guardian_name"],
            "student_name": item["student_name"],
            "class_name": item["class_name"],
            "school_name": school.name,
        }
        personalized = render_message_template(req.message_content, context)
        segments, _ = calculate_sms_segments(personalized)
        cost_tzs = segments * 25.0
        total_cost += cost_tzs

        rec = CampaignRecipient(
            campaign_id=campaign.id,
            guardian_id=item["guardian_id"],
            student_id=item["student_id"],
            phone_number=phone,
            personalized_text=personalized,
            segments=segments,
            status=MessageDeliveryStatus.QUEUED,
        )
        db.add(rec)

    campaign.total_cost_tzs = total_cost

    # Add Transactional Outbox Event
    outbox = OutboxEvent(
        aggregate_type="COMMUNICATION_CAMPAIGN",
        aggregate_id=str(campaign.id),
        event_type="CAMPAIGN_CREATED",
        payload={"campaign_id": str(campaign.id)},
    )
    db.add(outbox)
    db.commit()

    # Trigger Celery Worker async dispatch
    if not req.scheduled_at:
        dispatch_campaign_task.delay(str(campaign.id))

    return {
        "status": "success",
        "campaign_id": str(campaign.id),
        "recipient_count": len(seen_phones),
        "total_cost_tzs": total_cost,
        "is_scheduled": req.scheduled_at is not None,
    }


@router.get("")
def list_campaigns(
    class_group_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("communication:view_reports")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    query = select(CommunicationCampaign).where(CommunicationCampaign.school_id == school.id)
    if class_group_id:
        query = query.where(CommunicationCampaign.class_group_id == class_group_id)

    campaigns = db.execute(query.order_by(CommunicationCampaign.created_at.desc())).scalars().all()
    results = []
    for camp in campaigns:
        results.append({
            "id": str(camp.id),
            "title": camp.title,
            "message_content": camp.message_content,
            "targeting_mode": camp.targeting_mode.value,
            "status": camp.status.value,
            "recipient_count": camp.recipient_count,
            "delivered_count": camp.delivered_count,
            "failed_count": camp.failed_count,
            "total_cost_tzs": float(camp.total_cost_tzs),
            "created_at": camp.created_at.isoformat(),
        })
    return results


@router.get("/{campaign_id}")
def get_campaign_detail(
    campaign_id: uuid.UUID,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    camp = db.execute(select(CommunicationCampaign).where(CommunicationCampaign.id == campaign_id, CommunicationCampaign.school_id == school.id)).scalar_one_or_none()
    if not camp:
        raise HTTPException(status_code=404, detail="Campaign not found")

    recipients = db.execute(select(CampaignRecipient).where(CampaignRecipient.campaign_id == camp.id)).scalars().all()
    rec_list = []
    for r in recipients:
        rec_list.append({
            "id": str(r.id),
            "phone_number": r.phone_number,
            "guardian_name": r.guardian.full_name if r.guardian else "Unknown",
            "status": r.status.value,
            "segments": r.segments,
            "provider_message_id": r.provider_message_id,
            "text": r.personalized_text,
        })

    return {
        "id": str(camp.id),
        "title": camp.title,
        "message_content": camp.message_content,
        "status": camp.status.value,
        "targeting_mode": camp.targeting_mode.value,
        "recipient_count": camp.recipient_count,
        "delivered_count": camp.delivered_count,
        "failed_count": camp.failed_count,
        "total_cost_tzs": float(camp.total_cost_tzs),
        "recipients": rec_list,
    }


@router.post("/{campaign_id}/cancel")
def cancel_campaign(
    campaign_id: uuid.UUID,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    camp = db.execute(select(CommunicationCampaign).where(CommunicationCampaign.id == campaign_id, CommunicationCampaign.school_id == school.id)).scalar_one_or_none()
    if not camp:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if camp.status not in (CampaignStatus.DRAFT, CampaignStatus.SCHEDULED):
        raise HTTPException(status_code=400, detail="Cannot cancel campaign that has already started or completed")

    camp.status = CampaignStatus.CANCELLED
    db.commit()
    return {"status": "success", "message": "Campaign cancelled"}


@router.get("/templates/all")
def list_message_templates(
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")
    templates = db.execute(select(MessageTemplate).where(MessageTemplate.school_id == school.id)).scalars().all()
    return templates


@router.post("/templates")
def create_message_template(
    req: MessageTemplateCreate,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")
    template = MessageTemplate(
        school_id=school.id,
        name=req.name,
        category=req.category,
        language=req.language,
        content=req.content,
        variables=req.variables or [],
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return template
