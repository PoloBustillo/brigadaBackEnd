"""Assignment schemas."""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

from app.models.assignment import AssignmentStatus


class AssignmentBase(BaseModel):
    """Base assignment schema."""
    location: Optional[str] = None


class AssignmentCreate(AssignmentBase):
    """Create assignment."""
    user_id: int
    survey_id: int


class AssignmentUpdate(BaseModel):
    """Update assignment."""
    status: Optional[AssignmentStatus] = None
    location: Optional[str] = None


class AssignmentResponse(AssignmentBase):
    """Assignment response."""
    id: int
    user_id: int
    survey_id: int
    assigned_by: int
    status: AssignmentStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
