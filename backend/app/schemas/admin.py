from pydantic import BaseModel
from datetime import datetime
from app.models import UserRole


class UserAdminView(BaseModel):
    id:          int
    email:       str
    full_name:   str | None
    role:        UserRole
    is_active:   bool
    is_verified: bool
    created_at:  datetime

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    total:    int
    page:     int
    per_page: int
    users:    list[UserAdminView]


class UpdateRoleRequest(BaseModel):
    role: UserRole


class StatsResponse(BaseModel):
    total_users:     int
    active_users:    int
    verified_users:  int
    premium_users:   int
    waitlist_total:  int
    waitlist_pending: int


class ActivityLogView(BaseModel):
    id:         int
    action:     str
    ip_address: str | None
    created_at: datetime
    details:    str | None

    model_config = {"from_attributes": True}


class WaitlistEntryView(BaseModel):
    id:               int
    email:            str
    created_at:       datetime
    invited_at:       datetime | None
    invitation_token: str | None

    model_config = {"from_attributes": True}


class WaitlistListResponse(BaseModel):
    total:    int
    page:     int
    per_page: int
    entries:  list[WaitlistEntryView]