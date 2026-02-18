"""Assignment schemas."""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.models.assignment import AssignmentStatus


class AssignmentBase(BaseModel):
    """Base assignment schema."""
    location: Optional[str] = None
    notes: Optional[str] = None


class AssignmentCreate(AssignmentBase):
    """Create assignment — any active user (brigadista or encargado) can be assigned."""
    user_id: int
    survey_id: int


class AssignmentUpdate(BaseModel):
    """Update assignment."""
    status: Optional[AssignmentStatus] = None
    location: Optional[str] = None
    notes: Optional[str] = None

    def validate_status(self):
        if self.status and self.status not in (AssignmentStatus.ACTIVE, AssignmentStatus.INACTIVE):
            raise ValueError("Status must be active or inactive")
        return self


class AssignmentResponse(AssignmentBase):
    """Assignment response."""
    id: int
    user_id: int
    survey_id: int
    assigned_by: Optional[int] = None
    status: AssignmentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserMini(BaseModel):
    """Minimal user info for assignment detail."""
    id: int
    full_name: str
    email: str
    role: str
    model_config = ConfigDict(from_attributes=True)


class SurveyMini(BaseModel):
    """Minimal survey info for assignment detail."""
    id: int
    title: str
    model_config = ConfigDict(from_attributes=True)


class AssignmentDetailResponse(BaseModel):
    """Assignment with embedded user and survey names (admin list view)."""
    id: int
    user_id: int
    user: UserMini
    survey_id: int
    survey: SurveyMini
    assigned_by: Optional[int] = None
    assigned_by_user: Optional[UserMini] = None   # Who created the assignment
    status: AssignmentStatus
    location: Optional[str] = None
    notes: Optional[str] = None
    response_count: int = 0                        # How many times user submitted this survey
    created_at: datetime
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
