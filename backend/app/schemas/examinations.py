import uuid
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field
from app.models.examinations import ExamType, ResultStatus


class SubjectCreate(BaseModel):
    name: str
    code: str
    school_type: str = "PRIMARY"


class ExamCreate(BaseModel):
    academic_year_id: uuid.UUID
    academic_term_id: uuid.UUID
    name: str
    exam_type: ExamType = ExamType.MID_TERM
    start_date: date
    end_date: date


class ExamSubjectCreate(BaseModel):
    examination_id: uuid.UUID
    subject_id: uuid.UUID
    class_group_id: uuid.UUID
    max_score: float = 100.0
    pass_mark: float = 50.0


class StudentResultEntry(BaseModel):
    student_id: uuid.UUID
    score: float = Field(..., ge=0.0)
    remarks: Optional[str] = None


class BatchResultEntryRequest(BaseModel):
    examination_subject_id: uuid.UUID
    results: List[StudentResultEntry]


class ResultApprovalRequest(BaseModel):
    status: ResultStatus  # APPROVED or REJECTED
    comments: Optional[str] = None


class ResultPublicationRequest(BaseModel):
    examination_id: uuid.UUID
    class_group_id: uuid.UUID
    notify_parents_via_sms: bool = True
