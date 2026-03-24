from pydantic import BaseModel, EmailStr
from datetime import datetime
from app.models import UserRole


class UserProfile(BaseModel):
    id:          int
    email:       EmailStr
    full_name:   str | None
    role:        UserRole
    is_active:   bool
    is_verified: bool
    created_at:  datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None


class MessageResponse(BaseModel):
    message: str