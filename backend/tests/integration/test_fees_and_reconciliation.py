import random
import uuid
import pytest
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.identity import School, User, SchoolMembership, SchoolType, Role, RolePermission, Permission
from app.models.academic import Student, Gender, AcademicYear
from app.models.fees import FeeCategory, FeeStructure, FeeInvoice, FeeStatus, FeeAdjustment
from app.core.security import create_access_token, hash_password
from app.core.database import set_rls_tenant_context

client = TestClient(app)


def test_fee_reconciliation_workflow(db_session: Session, test_school: School):
    set_rls_tenant_context(db_session, test_school.id)

    # 1. Create User with fee:manage permission
    uid = uuid.uuid4().hex[:6]
    user = User(
        email=f"accountant_{uid}@test.ac.tz",
        phone_number=f"+255755{uid[:6]}",
        password_hash=hash_password("Pass123!"),
        full_name="Chief Accountant",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Link membership
    membership = SchoolMembership(school_id=test_school.id, user_id=user.id, is_active=True)
    db_session.add(membership)

    # Add fee:view and fee:manage permissions
    for p_code in ["fee:view", "fee:manage"]:
        perm = db_session.query(Permission).filter(Permission.code == p_code).first()
        if not perm:
            perm = Permission(code=p_code, module="fees", description=f"Permission {p_code}")
            db_session.add(perm)
            db_session.flush()

        role = Role(name=f"Role_{p_code}_{uid}", is_system_role=False)
        db_session.add(role)
        db_session.flush()

        rp = RolePermission(role_id=role.id, permission_id=perm.id)
        db_session.add(rp)
        db_session.flush()

        from app.models.identity import MembershipRole
        mr = MembershipRole(membership_id=membership.id, role_id=role.id)
        db_session.add(mr)
    db_session.commit()

    token = create_access_token({"sub": str(user.id), "email": user.email})
    headers = {"Authorization": f"Bearer {token}", "X-School-ID": str(test_school.id)}

    # 2. Create Student
    student = Student(
        school_id=test_school.id,
        admission_number=f"ACC-{uid}",
        first_name="Hassan",
        last_name="Mwinyi",
        gender=Gender.MALE,
        is_active=True,
    )
    db_session.add(student)
    db_session.flush()

    # 3. Create Fee Category & Structure
    cat = FeeCategory(school_id=test_school.id, name="Tuition", code=f"TUI_{uid}")
    db_session.add(cat)
    db_session.flush()

    from datetime import date
    year = AcademicYear(
        school_id=test_school.id,
        name=f"2026_{uid}",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        is_current=True,
    )
    db_session.add(year)
    db_session.flush()

    fee_struct = FeeStructure(
        school_id=test_school.id,
        academic_year_id=year.id,
        fee_category_id=cat.id,
        name="Term 1 Tuition",
        amount_tzs=500000.0,
        due_date=date(2026, 6, 30),
    )
    db_session.add(fee_struct)
    db_session.flush()

    # 4. Create an Invoice with an artificial discrepancy
    # Invoiced = 500,000; Total Payments = 0; Expected Balance = 500,000; Recorded Balance = 400,000 (Discrepancy = 100,000)
    inv = FeeInvoice(
        school_id=test_school.id,
        student_id=student.id,
        academic_year_id=year.id,
        invoice_number=f"INV-{uid}",
        total_amount_tzs=500000.0,
        balance_due_tzs=400000.0,  # Snapshot imported balance created discrepancy
        status=FeeStatus.PARTIALLY_PAID,
        due_date=date(2026, 6, 30),
    )
    db_session.add(inv)
    db_session.commit()

    # 5. Query Reconciliation Discrepancies Endpoint
    res = client.get("/api/v1/fees/reconciliation/discrepancies", headers=headers)
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total_discrepancies"] >= 1
    disc = next(d for d in data["discrepancies"] if d["invoice_id"] == str(inv.id))
    assert disc["total_invoiced_tzs"] == 500000.0
    assert disc["recorded_balance_tzs"] == 400000.0
    assert disc["discrepancy_tzs"] == 100000.0

    # 6. Apply Reconciliation Adjustment
    adj_payload = {
        "invoice_id": str(inv.id),
        "adjustment_type": "WAIVER",
        "amount_tzs": 100000.0,
        "reason": "Authorized hardship fee waiver for Semester 1",
    }
    adj_res = client.post("/api/v1/fees/reconciliation/apply-adjustment", data=adj_payload, headers=headers)
    assert adj_res.status_code == 200, adj_res.text
    adj_data = adj_res.json()
    assert adj_data["status"] == "success"
    assert adj_data["new_balance_tzs"] == 300000.0

    # 7. Verify audit record exists in database
    adj_record = db_session.query(FeeAdjustment).filter(FeeAdjustment.invoice_id == inv.id).first()
    assert adj_record is not None
    assert float(adj_record.amount_tzs) == 100000.0
    assert adj_record.adjustment_type == "WAIVER"
    assert adj_record.authorized_by_user_id == user.id
