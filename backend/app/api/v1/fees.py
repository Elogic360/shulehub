import uuid
from typing import List, Optional
from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_school, PermissionChecker
from app.models.identity import User, School
from app.models.academic import Student, ClassGroup, StudentEnrollment, EnrollmentStatus, Guardian, StudentGuardian
from app.models.fees import (
    FeeCategory,
    FeeStructure,
    FeeAssignment,
    StudentFeeAccount,
    FeeInvoice,
    FeeInvoiceItem,
    FeePayment,
    FeePaymentAllocation,
    FeeAdjustment,
    FeeReminderRule,
    FeeStatus,
    PaymentMethod,
)
from app.schemas.fees import (
    FeeCategoryCreate,
    FeeStructureCreate,
    FeeAssignmentCreate,
    PaymentRecordRequest,
    FeeReminderRuleCreate,
)

router = APIRouter()


# ==================== CATEGORIES & STRUCTURES ====================

@router.get("/categories")
def list_fee_categories(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")
    return db.execute(select(FeeCategory).where(FeeCategory.school_id == school.id)).scalars().all()


@router.post("/categories")
def create_fee_category(
    req: FeeCategoryCreate,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("fee:manage_structure")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    existing = db.execute(select(FeeCategory).where(FeeCategory.school_id == school.id, FeeCategory.code == req.code)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail=f"Category code {req.code} already exists")

    cat = FeeCategory(school_id=school.id, name=req.name, code=req.code.upper(), description=req.description)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.get("/structures")
def list_fee_structures(
    academic_year_id: Optional[uuid.UUID] = None,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")
    query = select(FeeStructure).where(FeeStructure.school_id == school.id)
    if academic_year_id:
        query = query.where(FeeStructure.academic_year_id == academic_year_id)
    structures = db.execute(query).scalars().all()
    results = []
    for s in structures:
        results.append({
            "id": str(s.id),
            "name": s.name,
            "category_name": s.category.name if s.category else None,
            "category_code": s.category.code if s.category else None,
            "amount_tzs": float(s.amount_tzs),
            "due_date": str(s.due_date),
            "academic_year_id": str(s.academic_year_id),
            "academic_term_id": str(s.academic_term_id) if s.academic_term_id else None,
        })
    return results


@router.post("/structures")
def create_fee_structure(
    req: FeeStructureCreate,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("fee:manage_structure")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    structure = FeeStructure(
        school_id=school.id,
        academic_year_id=req.academic_year_id,
        academic_term_id=req.academic_term_id,
        fee_category_id=req.fee_category_id,
        name=req.name,
        amount_tzs=req.amount_tzs,
        due_date=req.due_date,
    )
    db.add(structure)
    db.commit()
    db.refresh(structure)
    return structure


# ==================== FEE ASSIGNMENTS & INVOICES ====================

@router.post("/assignments")
def assign_fee(
    req: FeeAssignmentCreate,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("fee:assign")),
):
    """
    Assigns fee structure to an entire class or a specific student.
    Generates or updates student invoices and student fee accounts atomically.
    """
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    structure = db.execute(select(FeeStructure).where(FeeStructure.id == req.fee_structure_id, FeeStructure.school_id == school.id)).scalar_one_or_none()
    if not structure:
        raise HTTPException(status_code=404, detail="Fee structure not found")

    amount = req.amount_tzs or float(structure.amount_tzs)
    students_to_invoice: List[Student] = []

    if req.student_id:
        student = db.execute(select(Student).where(Student.id == req.student_id, Student.school_id == school.id)).scalar_one_or_none()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        students_to_invoice.append(student)
    elif req.class_group_id:
        enrollments = db.execute(
            select(StudentEnrollment).where(
                StudentEnrollment.class_group_id == req.class_group_id,
                StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE,
            )
        ).scalars().all()
        students_to_invoice = [e.student for e in enrollments]
    else:
        raise HTTPException(status_code=400, detail="Must specify either class_group_id or student_id")

    assigned_count = 0
    for st in students_to_invoice:
        # 1. Record FeeAssignment
        db.add(FeeAssignment(
            school_id=school.id,
            fee_structure_id=structure.id,
            class_group_id=req.class_group_id,
            student_id=st.id,
            amount_tzs=amount,
        ))

        # 2. Find or create active invoice for this student, year, and term
        invoice = db.execute(
            select(FeeInvoice).where(
                FeeInvoice.student_id == st.id,
                FeeInvoice.academic_year_id == structure.academic_year_id,
                FeeInvoice.academic_term_id == structure.academic_term_id,
                FeeInvoice.status.in_([FeeStatus.UNPAID, FeeStatus.PARTIALLY_PAID]),
            )
        ).scalar_one_or_none()

        if not invoice:
            inv_number = f"INV-{school.code}-{date.today().year}-{uuid.uuid4().hex[:6].upper()}"
            invoice = FeeInvoice(
                school_id=school.id,
                student_id=st.id,
                academic_year_id=structure.academic_year_id,
                academic_term_id=structure.academic_term_id,
                invoice_number=inv_number,
                total_amount_tzs=0.0,
                balance_due_tzs=0.0,
                status=FeeStatus.UNPAID,
                due_date=structure.due_date,
            )
            db.add(invoice)
            db.flush()

        # 3. Add Invoice Item
        inv_item = FeeInvoiceItem(
            invoice_id=invoice.id,
            fee_category_id=structure.fee_category_id,
            description=structure.name,
            amount_tzs=amount,
        )
        db.add(inv_item)

        invoice.total_amount_tzs = float(invoice.total_amount_tzs) + amount
        invoice.balance_due_tzs = float(invoice.balance_due_tzs) + amount

        # 4. Update StudentFeeAccount
        fee_acc = db.execute(
            select(StudentFeeAccount).where(
                StudentFeeAccount.student_id == st.id,
                StudentFeeAccount.academic_year_id == structure.academic_year_id,
            )
        ).scalar_one_or_none()

        if not fee_acc:
            fee_acc = StudentFeeAccount(
                school_id=school.id,
                student_id=st.id,
                academic_year_id=structure.academic_year_id,
                total_invoiced_tzs=0.0,
                total_paid_tzs=0.0,
                total_waived_tzs=0.0,
                outstanding_balance_tzs=0.0,
            )
            db.add(fee_acc)
            db.flush()

        fee_acc.total_invoiced_tzs = float(fee_acc.total_invoiced_tzs) + amount
        fee_acc.outstanding_balance_tzs = float(fee_acc.outstanding_balance_tzs) + amount

        assigned_count += 1

    db.commit()
    return {"status": "success", "students_assigned_count": assigned_count}


# ==================== PAYMENT RECORDING ====================

@router.post("/payments")
def record_payment(
    req: PaymentRecordRequest,
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("fee:record_payment")),
):
    """
    Records an immutable fee payment receipt and allocates funds against invoice items.
    Updates invoice balance and student fee ledger balances.
    """
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    student = db.execute(select(Student).where(Student.id == req.student_id, Student.school_id == school.id)).scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    receipt_no = f"RCT-{school.code}-{date.today().year}-{uuid.uuid4().hex[:6].upper()}"

    payment = FeePayment(
        school_id=school.id,
        student_id=student.id,
        invoice_id=req.invoice_id,
        receipt_number=receipt_no,
        payment_date=req.payment_date,
        amount_tzs=req.amount_tzs,
        payment_method=req.payment_method,
        transaction_reference=req.transaction_reference,
        recorded_by_user_id=current_user.id,
        notes=req.notes,
    )
    db.add(payment)
    db.flush()

    # Allocate payment to open invoice items
    amount_remaining_to_allocate = req.amount_tzs

    invoices_to_apply = []
    if req.invoice_id:
        inv = db.execute(select(FeeInvoice).where(FeeInvoice.id == req.invoice_id)).scalar_one_or_none()
        if inv:
            invoices_to_apply.append(inv)
    else:
        # Apply across open invoices oldest first
        invoices_to_apply = db.execute(
            select(FeeInvoice).where(
                FeeInvoice.student_id == student.id,
                FeeInvoice.status.in_([FeeStatus.UNPAID, FeeStatus.PARTIALLY_PAID, FeeStatus.OVERDUE]),
            ).order_by(FeeInvoice.due_date.asc())
        ).scalars().all()

    for inv in invoices_to_apply:
        if amount_remaining_to_allocate <= 0:
            break

        alloc_for_this_inv = 0.0
        for item in inv.items:
            if amount_remaining_to_allocate <= 0:
                break

            # Calculate already allocated amount for this item
            already_alloc = db.execute(
                select(func.coalesce(func.sum(FeePaymentAllocation.allocated_amount_tzs), 0.0))
                .where(FeePaymentAllocation.invoice_item_id == item.id)
            ).scalar()

            item_balance = float(item.amount_tzs) - float(already_alloc)
            if item_balance > 0:
                alloc_amt = min(amount_remaining_to_allocate, item_balance)
                db.add(FeePaymentAllocation(
                    payment_id=payment.id,
                    invoice_item_id=item.id,
                    allocated_amount_tzs=alloc_amt,
                ))
                alloc_for_this_inv += alloc_amt
                amount_remaining_to_allocate -= alloc_amt

        db.flush()

        # Update invoice balance and status
        inv.balance_due_tzs = max(0.0, float(inv.balance_due_tzs) - alloc_for_this_inv)
        if inv.balance_due_tzs == 0.0:
            inv.status = FeeStatus.PAID
        elif inv.balance_due_tzs < float(inv.total_amount_tzs):
            inv.status = FeeStatus.PARTIALLY_PAID

    # Update StudentFeeAccount ledger
    active_year = db.execute(select(StudentEnrollment).where(StudentEnrollment.student_id == student.id, StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE)).scalars().first()
    if active_year:
        fee_acc = db.execute(select(StudentFeeAccount).where(StudentFeeAccount.student_id == student.id, StudentFeeAccount.academic_year_id == active_year.academic_year_id)).scalar_one_or_none()
        if fee_acc:
            fee_acc.total_paid_tzs = float(fee_acc.total_paid_tzs) + req.amount_tzs
            fee_acc.outstanding_balance_tzs = max(0.0, float(fee_acc.total_invoiced_tzs) - float(fee_acc.total_paid_tzs) - float(fee_acc.total_waived_tzs))

    db.commit()
    return {
        "status": "success",
        "receipt_number": receipt_no,
        "amount_tzs": req.amount_tzs,
        "student_id": str(student.id),
    }


# ==================== LEDGER & REPORTS ====================

@router.get("/invoices")
def list_invoices(
    class_group_id: Optional[uuid.UUID] = None,
    fee_status: Optional[FeeStatus] = None,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("fee:view_reports")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    query = select(FeeInvoice).where(FeeInvoice.school_id == school.id)

    if class_group_id:
        query = query.join(StudentEnrollment, StudentEnrollment.student_id == FeeInvoice.student_id).where(
            StudentEnrollment.class_group_id == class_group_id,
            StudentEnrollment.enrollment_status == EnrollmentStatus.ACTIVE,
        )

    if fee_status:
        query = query.where(FeeInvoice.status == fee_status)

    invoices = db.execute(query.order_by(FeeInvoice.created_at.desc())).scalars().all()
    results = []
    for inv in invoices:
        st = db.execute(select(Student).where(Student.id == inv.student_id)).scalar_one_or_none()
        results.append({
            "id": str(inv.id),
            "invoice_number": inv.invoice_number,
            "student_id": str(inv.student_id),
            "student_name": f"{st.first_name} {st.last_name}" if st else "Unknown",
            "admission_number": st.admission_number if st else "",
            "total_amount_tzs": float(inv.total_amount_tzs),
            "balance_due_tzs": float(inv.balance_due_tzs),
            "status": inv.status.value,
            "due_date": str(inv.due_date),
            "items_count": len(inv.items),
        })
    return results


@router.get("/reports/summary")
def get_fee_summary(
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("fee:view_reports")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    total_invoiced = db.execute(select(func.coalesce(func.sum(FeeInvoice.total_amount_tzs), 0.0)).where(FeeInvoice.school_id == school.id)).scalar()
    total_balance_due = db.execute(select(func.coalesce(func.sum(FeeInvoice.balance_due_tzs), 0.0)).where(FeeInvoice.school_id == school.id)).scalar()
    total_collected = db.execute(select(func.coalesce(func.sum(FeePayment.amount_tzs), 0.0)).where(FeePayment.school_id == school.id)).scalar()

    paid_count = db.execute(select(func.count(FeeInvoice.id)).where(FeeInvoice.school_id == school.id, FeeInvoice.status == FeeStatus.PAID)).scalar()
    unpaid_count = db.execute(select(func.count(FeeInvoice.id)).where(FeeInvoice.school_id == school.id, FeeInvoice.status.in_([FeeStatus.UNPAID, FeeStatus.PARTIALLY_PAID, FeeStatus.OVERDUE]))).scalar()

    return {
        "total_invoiced_tzs": float(total_invoiced),
        "total_collected_tzs": float(total_collected),
        "total_outstanding_tzs": float(total_balance_due),
        "paid_invoices_count": paid_count,
        "pending_invoices_count": unpaid_count,
        "collection_rate_pct": round((float(total_collected) / float(total_invoiced) * 100.0), 1) if float(total_invoiced) > 0 else 0.0,
    }


# ==================== REMINDER RULES ====================

@router.get("/rules")
def list_fee_reminder_rules(school: School = Depends(get_current_school), db: Session = Depends(get_db)):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")
    return db.execute(select(FeeReminderRule).where(FeeReminderRule.school_id == school.id).order_by(FeeReminderRule.days_relative_to_due_date.asc())).scalars().all()


@router.post("/rules")
def create_fee_reminder_rule(
    req: FeeReminderRuleCreate,
    school: School = Depends(get_current_school),
    db: Session = Depends(get_db),
    _: bool = Depends(PermissionChecker("fee:send_reminders")),
):
    if not school:
        raise HTTPException(status_code=400, detail="School context required")

    rule = FeeReminderRule(
        school_id=school.id,
        days_relative_to_due_date=req.days_relative_to_due_date,
        reminder_channel=req.reminder_channel,
        is_enabled=req.is_enabled,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
