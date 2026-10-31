import uuid
from typing import Optional, List
from datetime import date, time
from pydantic import BaseModel, Field
from app.models.meetings import MeetingResponseStatus


class MeetingCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    meeting_date: date
    start_time: time
    end_time: time
    venue: str
    class_group_ids: Optional[List[uuid.UUID]] = None
    selected_guardian_ids: Optional[List[uuid.UUID]] = None
    send_sms_invitation: bool = True


class MeetingResponseSubmit(BaseModel):
    invitation_id: uuid.UUID
    response_status: MeetingResponseStatus
    comments: Optional[str] = None
    channel: str = "PORTAL"
