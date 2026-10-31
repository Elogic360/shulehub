import random
import uuid
import pytest
from starlette.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.models.identity import School, SchoolType
from app.models.academic import Guardian, Student, StudentGuardian, Gender, GuardianRelationship
from app.models.ussd import UssdOtpVerification
from app.api.v1.ussd import hash_otp
from app.core.database import set_rls_tenant_context

client = TestClient(app)


def test_ussd_unregistered_phone():
    phone = f"+255719{random.randint(100000, 999999)}"
    res = client.post(
        "/api/v1/ussd",
        data={
            "sessionId": f"ATUid_{uuid.uuid4().hex[:10]}",
            "serviceCode": "*384*55#",
            "phoneNumber": phone,
            "text": "",
        },
    )
    assert res.status_code == 200
    assert "END Karibu ShuleConnect" in res.text
    assert "haijasajiliwa" in res.text


def test_ussd_otp_generation_and_verification(db_session: Session, test_school: School):
    set_rls_tenant_context(db_session, test_school.id)

    # 1. Setup Guardian and Student
    phone = f"+255754{random.randint(100000, 999999)}"
    guardian = Guardian(
        school_id=test_school.id,
        full_name="Fatma Kassim",
        primary_phone=phone,
        preferred_language="sw",
    )
    db_session.add(guardian)
    db_session.flush()

    student = Student(
        school_id=test_school.id,
        admission_number=f"SC{random.randint(1000, 9999)}",
        first_name="Zuberi",
        last_name="Kassim",
        gender=Gender.MALE,
        ussd_access_id=f"{random.randint(100000, 999999)}",
        is_active=True,
    )
    db_session.add(student)
    db_session.flush()

    link = StudentGuardian(
        student_id=student.id,
        guardian_id=guardian.id,
        relationship_type=GuardianRelationship.MOTHER,
        is_fee_payer=True,
        can_receive_results=True,
    )
    db_session.add(link)
    db_session.commit()

    session_id = f"ATUid_{uuid.uuid4().hex[:10]}"

    # 2. Initial Dial: Should see School Main Menu
    res1 = client.post(
        "/api/v1/ussd",
        data={
            "sessionId": session_id,
            "serviceCode": "*384*55#",
            "phoneNumber": phone,
            "text": "",
        },
    )
    assert res1.status_code == 200
    assert "CON" in res1.text
    assert test_school.name in res1.text
    assert "Matokeo ya Ndani" in res1.text

    # 3. Select Option 1 (Matokeo ya Ndani): Should list students
    res2 = client.post(
        "/api/v1/ussd",
        data={
            "sessionId": session_id,
            "serviceCode": "*384*55#",
            "phoneNumber": phone,
            "text": "1",
        },
    )
    assert res2.status_code == 200
    assert "CON" in res2.text
    assert "Zuberi" in res2.text

    # 4. Select Student 1: Should trigger OTP issuance
    res3 = client.post(
        "/api/v1/ussd",
        data={
            "sessionId": session_id,
            "serviceCode": "*384*55#",
            "phoneNumber": phone,
            "text": "1*1",
        },
    )
    assert res3.status_code == 200
    assert "CON" in res3.text
    assert "Nambari ya uthibitisho imetumwa kwa SMS" in res3.text

    # 5. Retrieve OTP from database to test correct and incorrect attempts
    otp_record = (
        db_session.query(UssdOtpVerification)
        .filter(UssdOtpVerification.session_id == session_id)
        .first()
    )
    assert otp_record is not None
    assert otp_record.attempts_count == 0
    assert not otp_record.is_used

    # Set known hash for controlled verification
    known_otp = "842109"
    otp_record.otp_hash = hash_otp(known_otp)
    db_session.commit()

    # 6. Test Incorrect OTP: Should warn about remaining attempts
    res_bad = client.post(
        "/api/v1/ussd",
        data={
            "sessionId": session_id,
            "serviceCode": "*384*55#",
            "phoneNumber": phone,
            "text": "1*1*000000",
        },
    )
    assert res_bad.status_code == 200
    assert "CON Nambari si sahihi. Baki majaribio 2." in res_bad.text

    # 7. Test Correct OTP: Should reveal exam report
    res_good = client.post(
        "/api/v1/ussd",
        data={
            "sessionId": session_id,
            "serviceCode": "*384*55#",
            "phoneNumber": phone,
            "text": f"1*1*{known_otp}",
        },
    )
    assert res_good.status_code == 200
    assert "END" in res_good.text
    assert "Zuberi" in res_good.text


def test_ussd_multi_school_routing(db_session: Session, test_school: School):
    # Set RLS context to None for cross-tenant fixture setup
    set_rls_tenant_context(db_session, None)

    # 1. Create a second school
    uid2 = uuid.uuid4().hex[:5]
    school2 = School(
        name=f"St. Mary High {uid2}",
        code=f"SMH_{uid2}".upper(),
        registration_number=f"REG/SMH/{uid2}",
        school_type=SchoolType.SECONDARY,
        region="Arusha",
        district="Arusha Urban",
        contact_email=f"admin_{uid2}@stmary.ac.tz",
        contact_phone="+255755112233",
        is_verified=True,
    )
    db_session.add(school2)
    db_session.flush()

    # 2. Guardian with children in BOTH schools
    phone = f"+255768{random.randint(100000, 999999)}"
    guardian = Guardian(
        school_id=test_school.id,
        full_name="Baraka Mwamba",
        primary_phone=phone,
        preferred_language="sw",
    )
    db_session.add(guardian)
    db_session.flush()

    # Child in School 1
    std1 = Student(
        school_id=test_school.id,
        admission_number=f"PRI-{random.randint(100, 999)}",
        first_name="Neema",
        last_name="Mwamba",
        gender=Gender.FEMALE,
        ussd_access_id=f"{random.randint(100000, 999999)}",
        is_active=True,
    )
    # Child in School 2
    std2 = Student(
        school_id=school2.id,
        admission_number=f"SEC-{random.randint(100, 999)}",
        first_name="Emmanuel",
        last_name="Mwamba",
        gender=Gender.MALE,
        ussd_access_id=f"{random.randint(100000, 999999)}",
        is_active=True,
    )
    db_session.add_all([std1, std2])
    db_session.flush()

    link1 = StudentGuardian(student_id=std1.id, guardian_id=guardian.id, relationship_type=GuardianRelationship.FATHER)
    link2 = StudentGuardian(student_id=std2.id, guardian_id=guardian.id, relationship_type=GuardianRelationship.FATHER)
    db_session.add_all([link1, link2])
    db_session.commit()

    session_id = f"ATUid_multi_{uuid.uuid4().hex[:8]}"

    # 3. Dialing should present multi-school selection prompt
    res = client.post(
        "/api/v1/ussd",
        data={
            "sessionId": session_id,
            "serviceCode": "*384*55#",
            "phoneNumber": phone,
            "text": "",
        },
    )
    assert res.status_code == 200
    assert "CON Karibu ShuleConnect. Chagua Shule:" in res.text
    assert test_school.name in res.text
    assert school2.name in res.text
