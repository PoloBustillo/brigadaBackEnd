"""Response analytics router (Admin)."""
from typing import Annotated, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.response_service import ResponseService
from app.schemas.response import SurveyResponseDetail
from app.api.dependencies import AdminOrEncargado

router = APIRouter(prefix="/admin/responses", tags=["Admin - Responses"])


@router.get("/survey/{survey_id}", response_model=List[SurveyResponseDetail])
def get_survey_responses(
    survey_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: AdminOrEncargado,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Get all responses for a survey (Admin or Encargado).
    """
    service = ResponseService(db)
    return service.get_survey_responses(survey_id, skip=skip, limit=limit)


@router.get("/version/{version_id}", response_model=List[SurveyResponseDetail])
def get_version_responses(
    version_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: AdminOrEncargado,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Get all responses for a specific survey version (Admin or Encargado).
    """
    service = ResponseService(db)
    return service.get_version_responses(version_id, skip=skip, limit=limit)


@router.get("/{response_id}", response_model=SurveyResponseDetail)
def get_response(
    response_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: AdminOrEncargado
):
    """
    Get response details (Admin or Encargado).
    """
    service = ResponseService(db)
    return service.get_response(response_id)
