import pytest
import io
import uuid
from datetime import date
from app.core.database import set_rls_tenant_context
from app.services.import_engine import sanitize_cell_value, parse_spreadsheet_file, ImportProcessor
from app.models.imports import ImportBatch, ImportWorkflowType, ImportStatus, ImportRowStatus
from app.models.identity import School, User
from app.models.academic import AcademicYear, ClassGroup, AcademicLevel, Student

def test_formula_injection_sanitization():
    # Formulas starting with =, +, -, @, \t, \r must be stripped/escaped
    assert sanitize_cell_value("=1+1") == "1+1"
    assert sanitize_cell_value("=SUM(A1:A10)") == "SUM(A1:A10)"
    assert sanitize_cell_value("@IMPORT_DATA()") == "IMPORT_DATA()"
    assert sanitize_cell_value("+cmd|'/C calc'!A0") == "cmd|'/C calc'!A0"
    assert sanitize_cell_value("\t=2+2") == "2+2"
    assert sanitize_cell_value("Normal text") == "Normal text"
    assert sanitize_cell_value(123.45) == 123.45


def test_parse_csv_file_valid():
    csv_bytes = b"reg_no,full_name,gender\nSC001,Amina Juma,F\nSC002,Bakari Ali,M"
    rows, fmt = parse_spreadsheet_file(csv_bytes, "students.csv")
    assert fmt == "CSV"
    assert len(rows) == 2
    assert rows[0]["reg_no"] == "SC001"
    assert rows[0]["full_name"] == "Amina Juma"
    assert rows[0]["gender"] == "F"


def test_parse_csv_empty_file():
    csv_bytes = b""
    rows, fmt = parse_spreadsheet_file(csv_bytes, "empty.csv")
    assert len(rows) == 0


def test_student_import_workflow_validation(db_session, test_school, test_user):
    set_rls_tenant_context(db_session, test_school.id)
    # Create test academic year
    year = AcademicYear(
        school_id=test_school.id,
        name="2026",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        is_current=True,
    )
    db_session.add(year)
    db_session.flush()

    # Create batch
    batch = ImportBatch(
        school_id=test_school.id,
        workflow_type=ImportWorkflowType.STUDENT_REGISTRATION,
        status=ImportStatus.UPLOADED,
        created_by_id=test_user.id,
        metadata_info={},
    )
    db_session.add(batch)
    db_session.flush()

    # CSV with 1 valid row, 1 invalid gender row, 1 invalid phone row
    csv_content = (
        b"reg_no,full_name,gender,guardian_phone\n"
        b"SC991,Rashid Mussa,M,0754112233\n"
        b"SC992,Halima Zaid,X,0784998877\n"
        b"SC993,John Doe,M,12345\n"
    )

    processor = ImportProcessor(db_session, batch)
    processor.stage_file(csv_content, "students_batch.csv")

    assert batch.total_rows == 3
    assert batch.rejected_records_count == 2  # SC992 (invalid gender) and SC993 (invalid phone)
    assert batch.new_records_count == 1       # SC991 valid
    assert batch.status == ImportStatus.PREVIEW_READY

    # Commit batch
    res = processor.commit_batch(test_user.id)
    assert res["status"] == "COMMITTED"
    assert res["committed_rows"] == 1

    # Verify student exists in DB with USSD access ID
    student = db_session.query(Student).filter(Student.admission_number == "SC991").first()
    assert student is not None
    assert student.first_name == "Rashid"
    assert student.last_name == "Mussa"
    assert student.ussd_access_id is not None
    assert len(student.ussd_access_id) >= 6

    # Test Reversal / Rollback
    revert_res = processor.revert_batch(test_user.id)
    assert revert_res["status"] == "REVERTED"
    assert revert_res["reverted_records"] == 1

    # Verify student rolled back
    reverted_student = db_session.query(Student).filter(Student.admission_number == "SC991").first()
    assert reverted_student is None
