import uuid
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from app.models.identity import SchoolType


class LoginRequest(BaseModel):
    username: str = Field(..., description="Email or phone number")
    password: str = Field(..., min_length=6)
    school_id: Optional[uuid.UUID] = Field(None, description="Optional school context")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


from datetime import datetime


class RegisterSchoolRequest(BaseModel):
    school_name: str = Field(..., min_length=3, max_length=255)
    school_code: str = Field(..., min_length=2, max_length=50)
    school_type: SchoolType
    registration_number: Optional[str] = None
    region: str = "Dar es Salaam"
    district: Optional[str] = None
    contact_email: EmailStr
    contact_phone: str = Field(..., description="Phone number, e.g. +255712345678")
    owner_full_name: str = Field(..., min_length=3)
    owner_password: str = Field(..., min_length=8)
    invitation_token: Optional[str] = Field(None, description="Authorized registration invitation token from Super Admin")


class CreateSchoolInvitationRequest(BaseModel):
    target_school_name: Optional[str] = None
    target_contact_email: Optional[EmailStr] = None
    target_contact_phone: Optional[str] = None
    expires_in_days: int = Field(default=14, ge=1, le=90)
    notes: Optional[str] = None


class SchoolInvitationResponse(BaseModel):
    id: uuid.UUID
    token: str
    invitation_url: str
    target_school_name: Optional[str] = None
    target_contact_email: Optional[str] = None
    target_contact_phone: Optional[str] = None
    is_used: bool
    used_at: Optional[datetime] = None
    expires_at: datetime
    is_expired: bool
    created_at: datetime


class RegisterStaffRequest(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone_number: str
    password: str = Field(..., min_length=8)
    role_name: str  # "SCHOOL_ADMIN", "CLASS_TEACHER"
    preferred_language: str = "sw"


class RefreshTokenRequest(BaseModel):
    refresh_token: str
