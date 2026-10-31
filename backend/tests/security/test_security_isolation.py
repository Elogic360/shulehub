import random
import uuid
import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_cross_tenant_isolation():
    uid1 = uuid.uuid4().hex[:6].upper()
    uid2 = uuid.uuid4().hex[:6].upper()
    p1 = f"071{random.randint(1000000, 9999999)}"
    p2 = f"072{random.randint(1000000, 9999999)}"

    # 1. Register School A
    res_a = client.post("/api/v1/auth/register-school", json={
        "school_name": f"St. Anne Primary School {uid1}",
        "school_code": f"STA_{uid1}",
        "school_type": "PRIMARY",
        "contact_email": f"owner.anne_{uid1.lower()}@stanne.ac.tz",
        "contact_phone": p1,
        "owner_full_name": "Anne Owner",
        "owner_password": "SecurePassword123!",
    })
    assert res_a.status_code == 200, res_a.text
    token_a = res_a.json()["access_token"]
    school_a_id = res_a.json()["user"]["school_id"]

    # 2. Register School B
    res_b = client.post("/api/v1/auth/register-school", json={
        "school_name": f"Kilimanjaro Secondary {uid2}",
        "school_code": f"KIL_{uid2}",
        "school_type": "SECONDARY",
        "contact_email": f"owner.kili_{uid2.lower()}@kilima.ac.tz",
        "contact_phone": p2,
        "owner_full_name": "Kili Owner",
        "owner_password": "SecurePassword123!",
    })
    assert res_b.status_code == 200, res_b.text
    token_b = res_b.json()["access_token"]
    school_b_id = res_b.json()["user"]["school_id"]

    # 3. User from School A attempts to access School B via X-School-ID header
    forbidden_resp = client.get(
        "/api/v1/academic/levels",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-School-ID": school_b_id,
        },
    )
    # Must be 403 Forbidden
    assert forbidden_resp.status_code == 403


def test_unauthenticated_request_rejected():
    res = client.get("/api/v1/academic/levels")
    assert res.status_code == 401
