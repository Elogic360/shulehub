import uuid
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.communication import TargetingMode


class CampaignCreateRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    message_content: str = Field(..., min_length=2)
    targeting_mode: TargetingMode
    class_group_id: Optional[uuid.UUID] = None
    guardian_ids: Optional[List[uuid.UUID]] = None
    student_id: Optional[uuid.UUID] = None
    scheduled_at: Optional[datetime] = None


class MessageTemplateCreate(BaseModel):
    name: str
    category: str = "GENERAL"
    language: str = "sw"
    content: str
    variables: Optional[List[str]] = None


class DeliveryReportWebhook(BaseModel):
    id: str  # Africa's Talking message ID
    status: str
    phoneNumber: str
    networkCode: Optional[str] = None
    failureReason: Optional[str] = None
    retryCount: Optional[int] = None


class IncomingSmsWebhook(BaseModel):
    from_number: str = Field(..., alias="from")
    to: str
    text: str
    date: str
    id: str
    linkId: Optional[str] = None

    class Config:
        populate_by_name = True
