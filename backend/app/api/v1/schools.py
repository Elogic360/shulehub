import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_school, PermissionChecker
from app.models.identity import User, School, SchoolMembership, RoleType
from app.models.academic import Student, ClassGroup, Guardian
from app.models.communication import CommunicationCampaign
from app.models.fees import FeeInvoice, FeePayment, FeeStatus

router = APIRouter()


class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    region: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None


@router.get("/current")
def get_school_profile(school: School = Depends(get_current_school)):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")
    return {
        "id": str(school.id),
        "name": school.name,
        "code": school.code,
        "school_type": school.school_type.value,
        "registration_number": school.registration_number,
        "contact_email": school.contact_email,
        "contact_phone": school.contact_phone,
        "region": school.region,
        "district": school.district,
        "address": school.address,
        "is_verified": school.is_verified,
        "is_active": school.is_active,
    }


@router.put("/current")
def update_school_profile(
    req: SchoolUpdate,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("school:manage_settings")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    if req.name:
        school.name = req.name
    if req.contact_email:
        school.contact_email = req.contact_email
    if req.contact_phone:
        school.contact_phone = req.contact_phone
    if req.region:
        school.region = req.region
    if req.district:
        school.district = req.district
    if req.address:
        school.address = req.address

    db.commit()
    return {"status": "success", "message": "School settings updated"}


@router.get("/analytics")
def get_school_analytics(
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("school:view_analytics")),
):
    """
    Returns high-level operational statistics for School Owner & Administrator dashboards.
    """
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    total_students = db.execute(select(func.count(Student.id)).where(Student.school_id == school.id, Student.is_active == True)).scalar()
    total_classes = db.execute(select(func.count(ClassGroup.id)).where(ClassGroup.school_id == school.id)).scalar()
    total_guardians = db.execute(select(func.count(Guardian.id)).where(Guardian.school_id == school.id)).scalar()
    total_campaigns = db.execute(select(func.count(CommunicationCampaign.id)).where(CommunicationCampaign.school_id == school.id)).scalar()
    total_sms_cost = db.execute(select(func.coalesce(func.sum(CommunicationCampaign.total_cost_tzs), 0.0)).where(CommunicationCampaign.school_id == school.id)).scalar()

    total_invoiced = db.execute(select(func.coalesce(func.sum(FeeInvoice.total_amount_tzs), 0.0)).where(FeeInvoice.school_id == school.id)).scalar()
    total_collected = db.execute(select(func.coalesce(func.sum(FeePayment.amount_tzs), 0.0)).where(FeePayment.school_id == school.id)).scalar()
    total_outstanding = db.execute(select(func.coalesce(func.sum(FeeInvoice.balance_due_tzs), 0.0)).where(FeeInvoice.school_id == school.id)).scalar()

    return {
        "students_count": total_students,
        "classes_count": total_classes,
        "guardians_count": total_guardians,
        "campaigns_count": total_campaigns,
        "total_sms_expenditure_tzs": float(total_sms_cost),
        "total_fees_invoiced_tzs": float(total_invoiced),
        "total_fees_collected_tzs": float(total_collected),
        "total_fees_outstanding_tzs": float(total_outstanding),
    }


# ==================== SUPERADMIN PLATFORM ROUTES ====================

@router.get("/all")
def list_all_schools_superadmin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Superadmin access required")

    schools = db.execute(select(School).order_by(School.created_at.desc())).scalars().all()
    results = []
    for s in schools:
        student_cnt = db.execute(select(func.count(Student.id)).where(Student.school_id == s.id)).scalar()
        results.append({
            "id": str(s.id),
            "name": s.name,
            "code": s.code,
            "school_type": s.school_type.value,
            "contact_email": s.contact_email,
            "contact_phone": s.contact_phone,
            "is_verified": s.is_verified,
            "is_active": s.is_active,
            "students_count": student_cnt,
            "created_at": s.created_at.isoformat(),
        })
    return results


@router.post("/{school_id}/verify")
def verify_school(
    school_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Superadmin access required")

    school = db.execute(select(School).where(School.id == school_id)).scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    school.is_verified = True
    db.commit()
    return {"status": "success", "message": f"School {school.name} verified successfully"}
