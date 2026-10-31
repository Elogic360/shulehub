import random
import uuid
import pytest
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.identity import School, User, SchoolRegistrationInvitation
from app.core.security import create_access_token, hash_password
from app.core.database import set_rls_tenant_context

client = TestClient(app)


def test_school_registration_invitation_lifecycle(db_session: Session):
    set_rls_tenant_context(db_session, None)

    # 1. Create a Super Admin user
    uid = uuid.uuid4().hex[:6]
    superadmin = User(
        email=f"superadmin_{uid}@shuleconnect.co.tz",
        phone_number=f"+255788{uid[:6]}",
        password_hash=hash_password("SuperAdmin2026!"),
        full_name="Platform SuperAdmin",
        is_active=True,
        is_superadmin=True,
    )
    db_session.add(superadmin)
    db_session.commit()

    admin_token = create_access_token({"sub": str(superadmin.id), "email": superadmin.email})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Super Admin generates an invitation link for a school
    invite_payload = {
        "target_school_name": "Eagle Peak Secondary",
        "target_contact_email": f"head_{uid}@eaglepeak.ac.tz",
        "target_contact_phone": "+255754112233",
        "expires_in_days": 14,
        "notes": "Direct partnership onboarding",
    }
    create_res = client.post("/api/v1/auth/school-invitations", json=invite_payload, headers=admin_headers)
    assert create_res.status_code == 200, create_res.text
    invite_data = create_res.json()
    token = invite_data["token"]
    assert token is not None
    assert "/register-school?token=" in invite_data["invitation_url"]
    assert invite_data["is_used"] is False

    # 3. Public endpoint validates token
    val_res = client.get(f"/api/v1/auth/school-invitations/validate?token={token}")
    assert val_res.status_code == 200, val_res.text
    assert val_res.json()["valid"] is True
    assert val_res.json()["target_school_name"] == "Eagle Peak Secondary"

    # 4. Attempt to validate nonexistent token fails
    val_bad = client.get("/api/v1/auth/school-invitations/validate?token=nonexistent_token_123")
    assert val_bad.status_code == 404

    # 5. School registers using the valid invitation token
    school_code = f"EAG_{uid}".upper()
    owner_phone = f"+255716{random.randint(100000, 999999)}"
    reg_payload = {
        "school_name": "Eagle Peak Secondary",
        "school_code": school_code,
        "school_type": "SECONDARY",
        "contact_email": f"info_{uid}@eaglepeak.ac.tz",
        "contact_phone": owner_phone,
        "owner_full_name": "Dr. Joseph Mtemi",
        "owner_password": "EaglePassword2026!",
        "invitation_token": token,
    }
    reg_res = client.post("/api/v1/auth/register-school", json=reg_payload)
    assert reg_res.status_code == 200, reg_res.text
    auth_resp = reg_res.json()
    assert "access_token" in auth_resp
    assert auth_resp["user"]["school_name"] == "Eagle Peak Secondary"

    # 6. Verify invitation is now marked as USED in DB
    inv_in_db = db_session.query(SchoolRegistrationInvitation).filter(SchoolRegistrationInvitation.token == token).first()
    assert inv_in_db.is_used is True
    assert inv_in_db.used_at is not None
    assert inv_in_db.registered_school_id is not None

    # 7. Attempting to re-use the same token should fail
    reg_repeat = client.post("/api/v1/auth/register-school", json={
        **reg_payload,
        "school_code": f"EAG2_{uid}".upper(),
        "contact_phone": f"+255717{random.randint(100000, 999999)}",
    })
    assert reg_repeat.status_code == 400
    assert "kimeshatumika" in reg_repeat.text
