import json
import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_school, verify_class_teacher_access
from app.models.identity import User, School
from app.models.imports import (
    ImportBatch,
    ImportStagingRow,
    ImportValidationError,
    ImportChangeRecord,
    ImportWorkflowType,
    ImportStatus,
    ImportRowStatus,
)
from app.services.import_engine import ImportProcessor

router = APIRouter()


@router.get("/templates")
def get_import_templates(workflow_type: Optional[str] = Query(None)):
    """Returns column descriptions and sample CSV/XLSX template data for each workflow."""
    templates = {
        "STUDENT_REGISTRATION": {
            "columns": [
                {"name": "reg_no", "required": False, "description": "Student admission number (auto-generated if omitted)"},
                {"name": "full_name", "required": True, "description": "Full name (e.g. 'Amina Said Juma')"},
                {"name": "gender", "required": True, "description": "'M' or 'F'"},
                {"name": "date_of_birth", "required": False, "description": "YYYY-MM-DD"},
                {"name": "guardian_name", "required": False, "description": "Name of primary guardian"},
                {"name": "guardian_phone", "required": False, "description": "Tanzanian phone (e.g. '0754123456')"},
                {"name": "guardian_relationship", "required": False, "description": "FATHER, MOTHER, or GUARDIAN"},
            ],
            "sample_csv": "reg_no,full_name,gender,date_of_birth,guardian_name,guardian_phone,guardian_relationship\nSC2026/001,Amina Said,F,2014-05-12,Said Juma,0754123456,FATHER\nSC2026/002,Juma Bakari,M,2014-08-20,Asha Bakari,0784987654,MOTHER",
        },
        "EXAM_RESULTS": {
            "columns": [
                {"name": "admission_number", "required": True, "description": "Student admission number"},
                {"name": "student_name", "required": False, "description": "Student full name (for verification)"},
                {"name": "MATH", "required": False, "description": "Mathematics score (0-100 or ABS)"},
                {"name": "KISW", "required": False, "description": "Kiswahili score (0-100 or ABS)"},
                {"name": "ENG", "required": False, "description": "English score (0-100 or ABS)"},
                {"name": "SCI", "required": False, "description": "Science score (0-100 or ABS)"},
            ],
            "sample_csv": "admission_number,student_name,MATH,KISW,ENG,SCI\nSC2026/001,Amina Said,85,92,78,88\nSC2026/002,Juma Bakari,65,70,55,ABS",
        },
        "FEE_STRUCTURES": {
            "columns": [
                {"name": "academic_year", "required": False, "description": "Year (e.g. 2026)"},
                {"name": "term", "required": False, "description": "Term 1, Term 2, etc."},
                {"name": "class", "required": False, "description": "Class Group name"},
                {"name": "fee_category", "required": True, "description": "TUITION, TRANSPORT, MEALS, EXAMINATION"},
                {"name": "fee_description", "required": True, "description": "Description of the fee item"},
                {"name": "amount", "required": True, "description": "Amount in Tanzanian Shillings (TZS)"},
                {"name": "due_date", "required": False, "description": "YYYY-MM-DD"},
            ],
            "sample_csv": "fee_category,fee_description,amount,due_date\nTUITION,Standard 1 Tuition Term 1,450000,2026-03-31\nTRANSPORT,Route A Kinondoni Bus,150000,2026-03-31\nMEALS,Hot Lunch Plan,120000,2026-03-31",
        },
        "FEE_BALANCES": {
            "columns": [
                {"name": "admission_number", "required": True, "description": "Student admission number"},
                {"name": "student_name", "required": False, "description": "Student name"},
                {"name": "total_fees", "required": False, "description": "Total invoiced amount (TZS)"},
                {"name": "total_paid", "required": False, "description": "Total paid to date (TZS)"},
                {"name": "balance", "required": True, "description": "Outstanding balance due (TZS)"},
                {"name": "as_of_date", "required": False, "description": "Snapshot date (YYYY-MM-DD)"},
            ],
            "sample_csv": "admission_number,student_name,total_fees,total_paid,balance,as_of_date\nSC2026/001,Amina Said,450000,250000,200000,2026-10-31\nSC2026/002,Juma Bakari,450000,450000,0,2026-10-31",
        },
    }

    if workflow_type:
        wk = workflow_type.upper()
        if wk in templates:
            return {wk: templates[wk]}
        raise HTTPException(status_code=400, detail=f"Unknown workflow type '{workflow_type}'")
    return templates


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_import_file(
    file: UploadFile = File(...),
    workflow_type: ImportWorkflowType = Form(...),
    class_group_id: Optional[uuid.UUID] = Form(None),
    metadata_json: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
):
    """
    Step 1: Upload and stage an Excel (.xlsx) or CSV spreadsheet.
    Parses content, prevents formula injection, validates rows, and returns preview statistics.
    """
    if class_group_id and not verify_class_teacher_access(class_group_id, current_user, school.id, db):
        raise HTTPException(status_code=403, detail="Unauthorized access to specified class group")

    metadata = json.loads(metadata_json) if metadata_json else {}

    # Initialize batch record
    batch = ImportBatch(
        school_id=school.id,
        class_group_id=class_group_id,
        workflow_type=workflow_type,
        status=ImportStatus.UPLOADED,
        created_by_id=current_user.id,
        metadata_info=metadata,
    )
    db.add(batch)
    db.flush()

    content_bytes = await file.read()
    processor = ImportProcessor(db, batch)
    try:
        processor.stage_file(content_bytes, file.filename)
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "batch_id": str(batch.id),
        "status": batch.status.value,
        "workflow_type": batch.workflow_type.value,
        "total_rows": batch.total_rows,
        "new_records": batch.new_records_count,
        "updated_records": batch.updated_records_count,
        "rejected_records": batch.rejected_records_count,
        "duplicate_records": batch.duplicate_records_count,
        "warning_count": batch.warning_count,
    }


@router.get("/{batch_id}")
def get_import_batch_status(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    school: School = Depends(get_current_school),
):
    """Retrieves batch processing details, stats and status."""
    batch = db.execute(
        select(ImportBatch).where(ImportBatch.id == batch_id, ImportBatch.school_id == school.id)
    ).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")

    return {
        "id": str(batch.id),
        "workflow_type": batch.workflow_type.value,
        "status": batch.status.value,
        "total_rows": batch.total_rows,
        "new_records": batch.new_records_count,
        "updated_records": batch.updated_records_count,
        "unchanged_records": batch.unchanged_records_count,
        "rejected_records": batch.rejected_records_count,
        "duplicate_records": batch.duplicate_records_count,
        "warning_count": batch.warning_count,
        "created_at": batch.created_at.isoformat(),
        "committed_at": batch.committed_at.isoformat() if batch.committed_at else None,
        "reverted_at": batch.reverted_at.isoformat() if batch.reverted_at else None,
    }


@router.get("/{batch_id}/preview")
def get_import_preview(
    batch_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    school: School = Depends(get_current_school),
):
    """Returns staged preview rows with validation status, mapped values and warnings."""
    batch = db.execute(
        select(ImportBatch).where(ImportBatch.id == batch_id, ImportBatch.school_id == school.id)
    ).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")

    rows = db.execute(
        select(ImportStagingRow)
        .where(ImportStagingRow.batch_id == batch.id)
        .order_by(ImportStagingRow.row_number)
        .limit(limit)
        .offset(offset)
    ).scalars().all()

    return {
        "batch_id": str(batch.id),
        "total_rows": batch.total_rows,
        "status": batch.status.value,
        "rows": [
            {
                "row_number": r.row_number,
                "status": r.status.value,
                "action_type": r.action_type,
                "data": r.mapped_data,
                "error_summary": r.error_summary,
            }
            for r in rows
        ],
    }


@router.get("/{batch_id}/errors")
def get_import_errors(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    school: School = Depends(get_current_school),
):
    """Returns detailed row-level error reports with column names and error codes."""
    batch = db.execute(
        select(ImportBatch).where(ImportBatch.id == batch_id, ImportBatch.school_id == school.id)
    ).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")

    errors = db.execute(
        select(ImportValidationError)
        .where(ImportValidationError.batch_id == batch.id)
        .order_by(ImportValidationError.row_number)
    ).scalars().all()

    return {
        "batch_id": str(batch.id),
        "total_errors": len(errors),
        "errors": [
            {
                "row_number": e.row_number,
                "column_name": e.column_name,
                "error_code": e.error_code,
                "error_message": e.error_message,
                "raw_value": e.raw_value,
            }
            for e in errors
        ],
    }


@router.post("/{batch_id}/approve")
def approve_import_batch(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
):
    """Marks a validated batch as approved for commitment."""
    batch = db.execute(
        select(ImportBatch).where(ImportBatch.id == batch_id, ImportBatch.school_id == school.id)
    ).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")

    if batch.status != ImportStatus.PREVIEW_READY:
        raise HTTPException(status_code=400, detail=f"Cannot approve batch in status '{batch.status.value}'")

    batch.status = ImportStatus.APPROVED
    batch.approved_by_id = current_user.id
    db.commit()

    return {"batch_id": str(batch.id), "status": batch.status.value, "message": "Batch approved for commit"}


@router.post("/{batch_id}/commit")
def commit_import_batch(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
):
    """
    Step 2: Atomically commits the staged valid records into permanent database tables.
    Generates change audit records allowing future reversal.
    """
    batch = db.execute(
        select(ImportBatch).where(ImportBatch.id == batch_id, ImportBatch.school_id == school.id)
    ).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")

    processor = ImportProcessor(db, batch)
    try:
        result = processor.commit_batch(current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@router.post("/{batch_id}/revert")
def revert_import_batch(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    school: School = Depends(get_current_school),
):
    """Compensating rollback of a committed batch using import_change_records."""
    batch = db.execute(
        select(ImportBatch).where(ImportBatch.id == batch_id, ImportBatch.school_id == school.id)
    ).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Import batch not found")

    processor = ImportProcessor(db, batch)
    try:
        result = processor.revert_batch(current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@router.get("/history/list")
def list_import_history(
    limit: int = 20,
    offset: int = 0,
    workflow_type: Optional[ImportWorkflowType] = Query(None),
    db: Session = Depends(get_db),
    school: School = Depends(get_current_school),
):
    """Returns past import batches and audit outcomes for the school."""
    query = select(ImportBatch).where(ImportBatch.school_id == school.id)
    if workflow_type:
        query = query.where(ImportBatch.workflow_type == workflow_type)
    query = query.order_by(desc(ImportBatch.created_at)).limit(limit).offset(offset)

    batches = db.execute(query).scalars().all()
    return [
        {
            "id": str(b.id),
            "workflow_type": b.workflow_type.value,
            "status": b.status.value,
            "total_rows": b.total_rows,
            "new_records": b.new_records_count,
            "updated_records": b.updated_records_count,
            "rejected_records": b.rejected_records_count,
            "created_at": b.created_at.isoformat(),
            "committed_at": b.committed_at.isoformat() if b.committed_at else None,
            "reverted_at": b.reverted_at.isoformat() if b.reverted_at else None,
        }
        for b in batches
    ]
