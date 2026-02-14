"""Survey service."""
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.survey_repository import SurveyRepository
from app.models.survey import Survey, SurveyVersion
from app.schemas.survey import SurveyCreate, SurveyUpdate


class SurveyService:
    """Survey business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.survey_repo = SurveyRepository(db)
    
    def create_survey(self, survey_data: SurveyCreate, created_by: int) -> Survey:
        """
        Create a new survey with initial version.
        
        Creates survey, first version, and all questions with options.
        """
        # Create survey
        survey = self.survey_repo.create(
            title=survey_data.title,
            description=survey_data.description,
            created_by=created_by
        )
        
        # Create first version
        version = self.survey_repo.create_version(
            survey_id=survey.id,
            version_number=1,
            change_summary="Initial version"
        )
        
        # Create questions and options
        for question_data in survey_data.questions:
            question = self.survey_repo.create_question(
                version_id=version.id,
                question_text=question_data.question_text,
                question_type=question_data.question_type,
                order=question_data.order,
                is_required=question_data.is_required,
                validation_rules=question_data.validation_rules
            )
            
            # Create answer options if applicable
            if question_data.options:
                for option_data in question_data.options:
                    self.survey_repo.create_answer_option(
                        question_id=question.id,
                        option_text=option_data.option_text,
                        order=option_data.order
                    )
        
        # Refresh to get all relationships
        return self.survey_repo.get_by_id(survey.id)
    
    def get_survey(self, survey_id: int) -> Survey:
        """
        Get survey by ID.
        
        Raises:
            HTTPException: If survey not found
        """
        survey = self.survey_repo.get_by_id(survey_id)
        
        if not survey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
        
        return survey
    
    def get_surveys(self, skip: int = 0, limit: int = 100, 
                    is_active: Optional[bool] = None) -> List[Survey]:
        """Get list of surveys."""
        return self.survey_repo.get_all(skip=skip, limit=limit, is_active=is_active)
    
    def update_survey(self, survey_id: int, survey_data: SurveyUpdate) -> Survey:
        """
        Update survey - creates a new version if questions are modified.
        
        Raises:
            HTTPException: If survey not found
        """
        survey = self.get_survey(survey_id)
        
        # Update basic fields
        if survey_data.title or survey_data.description:
            self.survey_repo.update(
                survey_id=survey_id,
                title=survey_data.title,
                description=survey_data.description
            )
        
        # If questions are being updated, create new version
        if survey_data.questions:
            latest_version = self.survey_repo.get_latest_version(survey_id)
            new_version_number = (latest_version.version_number + 1) if latest_version else 1
            
            # Create new version
            version = self.survey_repo.create_version(
                survey_id=survey_id,
                version_number=new_version_number,
                change_summary=survey_data.change_summary or f"Version {new_version_number}"
            )
            
            # Create questions and options
            for question_data in survey_data.questions:
                question = self.survey_repo.create_question(
                    version_id=version.id,
                    question_text=question_data.question_text,
                    question_type=question_data.question_type,
                    order=question_data.order,
                    is_required=question_data.is_required,
                    validation_rules=question_data.validation_rules
                )
                
                if question_data.options:
                    for option_data in question_data.options:
                        self.survey_repo.create_answer_option(
                            question_id=question.id,
                            option_text=option_data.option_text,
                            order=option_data.order
                        )
        
        return self.survey_repo.get_by_id(survey_id)
    
    def delete_survey(self, survey_id: int) -> None:
        """
        Soft delete survey.
        
        Raises:
            HTTPException: If survey not found
        """
        success = self.survey_repo.delete(survey_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey not found"
            )
    
    def publish_version(self, version_id: int) -> SurveyVersion:
        """
        Publish a survey version.
        
        Raises:
            HTTPException: If version not found
        """
        version = self.survey_repo.publish_version(version_id)
        
        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey version not found"
            )
        
        return version
    
    def get_latest_published_version(self, survey_id: int) -> SurveyVersion:
        """
        Get latest published version for mobile app.
        
        Raises:
            HTTPException: If no published version found
        """
        latest = self.survey_repo.get_latest_version(survey_id)
        
        if not latest or not latest.is_published:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No published version available"
            )
        
        return latest
