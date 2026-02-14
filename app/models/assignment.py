"""Assignment models."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.core.database import Base


class AssignmentStatus(str, Enum):
    """Assignment status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Assignment(Base):
    """
    Assignment model - links users to surveys.
    Encargados assign surveys to Brigadistas.
    """
    
    __tablename__ = "assignments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by = Column(Integer, nullable=False)  # User ID of who assigned it
    status = Column(SQLEnum(AssignmentStatus), default=AssignmentStatus.PENDING, nullable=False)
    location = Column(String, nullable=True)  # Optional: area/zone for assignment
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="assignments")
    survey = relationship("Survey", back_populates="assignments")
    
    # Ensure a user can't be assigned the same survey multiple times (unless completed)
    __table_args__ = (
        UniqueConstraint('user_id', 'survey_id', name='uq_user_survey'),
    )
    
    def __repr__(self):
        return f"<Assignment(id={self.id}, user_id={self.user_id}, survey_id={self.survey_id}, status={self.status})>"
