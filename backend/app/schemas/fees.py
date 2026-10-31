import uuid
from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field
from app.models.fees import PaymentMethod


class FeeCategoryCreate(BaseModel):
    name: str  # e.g., "Tuition", "Transport", "Meals"
    code: str  # e.g., "TUITION"
    description: Optional[str] = None


class FeeStructureCreate(BaseModel):
    academic_year_id: uuid.UUID
    academic_term_id: Optional[uuid.UUID] = None
    fee_category_id: uuid.UUID
    name: str
    amount_tzs: float = Field(..., gt=0)
    due_date: date


class FeeAssignmentCreate(BaseModel):
    fee_structure_id: uuid.UUID
    class_group_id: Optional[uuid.UUID] = None  # Assign to whole class
    student_id: Optional[uuid.UUID] = None       # Assign to individual student
    amount_tzs: Optional[float] = None          # Override amount if different


class PaymentRecordRequest(BaseModel):
    student_id: uuid.UUID
    invoice_id: Optional[uuid.UUID] = None
    payment_date: date
    amount_tzs: float = Field(..., gt=0)
    payment_method: PaymentMethod = PaymentMethod.BANK_TRANSFER
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None


class FeeReminderRuleCreate(BaseModel):
    days_relative_to_due_date: int  # e.g. -7, 0, 7
    reminder_channel: str = "SMS"
    is_enabled: bool = True
