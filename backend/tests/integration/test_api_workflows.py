import random
import uuid
import pytest
from starlette.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_full_school_lifecycle_and_features():
    uid = uuid.uuid4().hex[:6].upper()
    code = f"SUN_{uid}"
    owner_phone = f"0754{random.randint(100000, 999999)}"
    teacher_phone = f"0715{random.randint(100000, 999999)}"
    guardian_contact = f"0745{random.randint(100000, 999999)}"

    # 1. School Registration
    reg_payload = {
        "school_name": f"Sunrise Academy {uid}",
        "school_code": code,
        "school_type": "PRIMARY",
        "region": "Dar es Salaam",
        "district": "Kinondoni",
        "contact_email": f"principal_{uid.lower()}@sunrise.ac.tz",
        "contact_phone": owner_phone,
        "owner_full_name": "Ester Msuya",
        "owner_password": "OwnerPassword2026!",
    }
    reg_res = client.post("/api/v1/auth/register-school", json=reg_payload)
    assert reg_res.status_code == 200, reg_res.text
    auth_data = reg_res.json()
    token = auth_data["access_token"]
    school_id = auth_data["user"]["school_id"]
    headers = {"Authorization": f"Bearer {token}", "X-School-ID": school_id}

    # 2. Verify Academic Levels (Primary has 6 standard levels)
    levels_res = client.get("/api/v1/academic/levels", headers=headers)
    assert levels_res.status_code == 200
    levels = levels_res.json()
    assert len(levels) == 6
    std1_level_id = levels[0]["id"]

    # 3. Fetch default 2026 academic year
    years_res = client.get("/api/v1/academic/years", headers=headers)
    assert years_res.status_code == 200
    years = years_res.json()
    assert len(years) >= 1
    year_id = years[0]["id"]

    # 4. Create Class Group (Standard 1A)
    class_res = client.post("/api/v1/academic/classes", json={
        "academic_level_id": std1_level_id,
        "academic_year_id": year_id,
        "name": "Standard 1A",
        "stream": "A",
        "capacity": 45,
    }, headers=headers)
    assert class_res.status_code == 200
    class_id = class_res.json()["id"]

    # 5. Register Teacher Staff
    staff_res = client.post("/api/v1/auth/register-staff", json={
        "full_name": "Mwl. Juma Rashidi",
        "email": f"juma_{uid.lower()}@sunrise.ac.tz",
        "phone_number": teacher_phone,
        "password": "TeacherPassword2026!",
        "role_name": "CLASS_TEACHER",
    }, headers=headers)
    assert staff_res.status_code == 200
    teacher_id = staff_res.json()["user_id"]

    # 6. Assign Teacher to Standard 1A
    assign_res = client.post("/api/v1/academic/classes/assign-teacher", json={
        "class_group_id": class_id,
        "teacher_user_id": teacher_id,
        "academic_year_id": year_id,
    }, headers=headers)
    assert assign_res.status_code == 200

    # 7. Register Student & Linked Guardian
    adm_num = f"SR/{uid}/001"
    student_res = client.post("/api/v1/students", json={
        "admission_number": adm_num,
        "first_name": "Kelvin",
        "last_name": "Mwangi",
        "gender": "MALE",
        "class_group_id": class_id,
        "academic_year_id": year_id,
        "guardian": {
            "full_name": "Mary Mwangi",
            "primary_phone": guardian_contact,
            "preferred_language": "sw",
            "relationship_type": "MOTHER",
        },
    }, headers=headers)
    assert student_res.status_code == 200
    student_id = student_res.json()["student_id"]

    # 8. List students and verify
    students_list_res = client.get(f"/api/v1/students?class_group_id={class_id}", headers=headers)
    assert students_list_res.status_code == 200
    students_list = students_list_res.json()
    assert len(students_list) == 1
    assert students_list[0]["admission_number"] == adm_num
    guardian_id = students_list[0]["guardians"][0]["id"]
    guardian_phone = students_list[0]["guardians"][0]["primary_phone"]

    # 9. Preview Campaign
    preview_res = client.post("/api/v1/communication/preview", json={
        "title": "Karibu Muhula Mpya",
        "message_content": "Habari {{parent_name}}, shule inafungua rasmi tarehe 12/01/2026 kwa mwanafunzi {{student_name}}.",
        "targeting_mode": "CLASS_BULK",
        "class_group_id": class_id,
    }, headers=headers)
    assert preview_res.status_code == 200
    assert preview_res.json()["unique_recipients_count"] == 1

    # 10. Dispatch Campaign
    camp_res = client.post("/api/v1/communication", json={
        "title": "Tangazo la Kufungua Shule",
        "message_content": "Habari {{parent_name}}, shule inafungua rasmi tarehe 12/01/2026 kwa mwanafunzi {{student_name}}.",
        "targeting_mode": "CLASS_BULK",
        "class_group_id": class_id,
    }, headers=headers)
    assert camp_res.status_code == 200
    campaign_id = camp_res.json()["campaign_id"]

    # 11. Test Webhook Delivery Report Callback
    dlr_res = client.post("/api/v1/webhooks/delivery-reports", data={
        "id": "ATXid_test_message_123",
        "status": "Success",
        "phoneNumber": guardian_phone,
        "networkCode": "64002",
    })
    assert dlr_res.status_code == 200

    # 12. Test USSD flow for parent
    # Step 1: Root menu
    ussd_root = client.post("/api/v1/ussd", data={
        "sessionId": "ATSession_12345",
        "serviceCode": "*384*55#",
        "phoneNumber": guardian_phone,
        "text": "",
    })
    assert ussd_root.status_code == 200
    assert "CON" in ussd_root.text
    assert "Matokeo ya Ndani" in ussd_root.text

    # Step 2: Select 4 (Fee balance)
    ussd_fees = client.post("/api/v1/ussd", data={
        "sessionId": "ATSession_12345",
        "serviceCode": "*384*55#",
        "phoneNumber": guardian_phone,
        "text": "4",
    })
    assert ussd_fees.status_code == 200
    assert "Salio la Ada" in ussd_fees.text

    # 13. Create Fee Category, Structure, and Assign
    cat_res = client.post("/api/v1/fees/categories", json={
        "name": "Ada ya Masomo (Tuition)",
        "code": "TUITION",
    }, headers=headers)
    assert cat_res.status_code == 200
    cat_id = cat_res.json()["id"]

    struct_res = client.post("/api/v1/fees/structures", json={
        "academic_year_id": year_id,
        "fee_category_id": cat_id,
        "name": "Tuition Term 1 2026",
        "amount_tzs": 450000.0,
        "due_date": "2026-02-15",
    }, headers=headers)
    assert struct_res.status_code == 200
    struct_id = struct_res.json()["id"]

    assign_fee_res = client.post("/api/v1/fees/assignments", json={
        "fee_structure_id": struct_id,
        "class_group_id": class_id,
    }, headers=headers)
    assert assign_fee_res.status_code == 200
    assert assign_fee_res.json()["students_assigned_count"] == 1

    # 14. Record Payment
    pay_res = client.post("/api/v1/fees/payments", json={
        "student_id": student_id,
        "payment_date": "2026-01-20",
        "amount_tzs": 250000.0,
        "payment_method": "BANK_TRANSFER",
        "transaction_reference": "CRDB-TXN-884920",
        "notes": "First installment payment",
    }, headers=headers)
    assert pay_res.status_code == 200
    assert "receipt_number" in pay_res.json()

    # 15. Check Invoices Summary
    inv_res = client.get("/api/v1/fees/invoices", headers=headers)
    assert inv_res.status_code == 200
    invoices = inv_res.json()
    assert len(invoices) >= 1
    # Balance due should be 450,000 - 250,000 = 200,000
    assert invoices[0]["balance_due_tzs"] == 200000.0
    assert invoices[0]["status"] == "PARTIALLY_PAID"
