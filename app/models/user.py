"""User model."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum

from app.core.database import Base


class UserRole(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    ENCARGADO = "encargado"
    BRIGADISTA = "brigadista"


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.BRIGADISTA)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    assignments = relationship("Assignment", back_populates="user", cascade="all, delete-orphan")
    survey_responses = relationship("SurveyResponse", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
