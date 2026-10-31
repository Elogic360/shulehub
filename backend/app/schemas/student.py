import uuid
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, EmailStr, Field
from app.models.academic import Gender, GuardianRelationship


class GuardianCreate(BaseModel):
    full_name: str
    primary_phone: str
    secondary_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    preferred_language: str = "sw"
    relationship_type: GuardianRelationship = GuardianRelationship.GUARDIAN
    is_fee_payer: bool = True
    can_receive_results: bool = True


class StudentCreate(BaseModel):
    admission_number: str
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    gender: Gender
    date_of_birth: Optional[date] = None
    class_group_id: uuid.UUID
    academic_year_id: uuid.UUID
    guardian: Optional[GuardianCreate] = None


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[Gender] = None
    date_of_birth: Optional[date] = None
    is_active: Optional[bool] = None


class GuardianLinkRequest(BaseModel):
    student_id: uuid.UUID
    guardian_id: uuid.UUID
    relationship_type: GuardianRelationship
    is_fee_payer: bool = True
    can_receive_results: bool = True
