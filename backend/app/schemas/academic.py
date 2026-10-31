import uuid
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field


class AcademicLevelCreate(BaseModel):
    name: str  # e.g., "Standard 1" or "Form 1"
    code: str  # e.g., "STD_1"
    sequence_order: int = 1
    school_type: str = "PRIMARY"


class AcademicYearCreate(BaseModel):
    name: str  # e.g., "2026"
    start_date: date
    end_date: date
    is_current: bool = True


class AcademicTermCreate(BaseModel):
    academic_year_id: uuid.UUID
    name: str  # e.g., "Term 1"
    term_number: int = 1
    start_date: date
    end_date: date
    is_current: bool = True


class ClassGroupCreate(BaseModel):
    academic_level_id: uuid.UUID
    academic_year_id: uuid.UUID
    name: str  # e.g., "Standard 1A"
    stream: Optional[str] = "A"
    capacity: int = 50


class ClassTeacherAssignRequest(BaseModel):
    class_group_id: uuid.UUID
    teacher_user_id: uuid.UUID
    academic_year_id: uuid.UUID
