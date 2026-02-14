"""Survey response models."""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SurveyResponse(Base):
    """
    Survey response model - represents a completed survey submission.
    Linked to a specific survey version for immutability.
    """
    
    __tablename__ = "survey_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    version_id = Column(Integer, ForeignKey("survey_versions.id", ondelete="RESTRICT"), nullable=False)
    
    # Offline sync support
    client_id = Column(String, nullable=False, unique=True, index=True)  # UUID from mobile app
    location = Column(JSON, nullable=True)  # {lat, lng, accuracy, timestamp}
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=False)
    synced_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Metadata
    device_info = Column(JSON, nullable=True)  # Device type, OS version, app version
    
    # Relationships
    user = relationship("User", back_populates="survey_responses")
    version = relationship("SurveyVersion", back_populates="responses")
    answers = relationship("QuestionAnswer", back_populates="response", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SurveyResponse(id={self.id}, user_id={self.user_id}, version_id={self.version_id})>"


class QuestionAnswer(Base):
    """
    Individual answer to a question within a survey response.
    Stores answers in flexible JSON format to accommodate all question types.
    """
    
    __tablename__ = "question_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("survey_responses.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False)
    
    # Flexible answer storage
    answer_value = Column(JSON, nullable=True)  # Can be string, number, array, or object
    
    # For photo/signature questions
    media_url = Column(String, nullable=True)
    
    # Timestamps
    answered_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    response = relationship("SurveyResponse", back_populates="answers")
    question = relationship("Question", back_populates="answers")
    
    def __repr__(self):
        return f"<QuestionAnswer(id={self.id}, question_id={self.question_id})>"
