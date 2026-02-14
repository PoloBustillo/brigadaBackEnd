"""Mobile app routers for brigadistas."""
from typing import Annotated, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.survey_service import SurveyService
from app.services.response_service import ResponseService
from app.schemas.survey import SurveyVersionResponse
from app.schemas.response import SurveyResponseCreate, SurveyResponseDetail
from app.api.dependencies import BrigadistaUser

router = APIRouter(prefix="/mobile", tags=["Mobile App"])


@router.get("/surveys/{survey_id}/latest", response_model=SurveyVersionResponse)
def get_latest_survey_version(
    survey_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: BrigadistaUser
):
    """
    Get latest published survey version for mobile app.
    
    Used by mobile app to download survey structure.
    """
    service = SurveyService(db)
    return service.get_latest_published_version(survey_id)


@router.post("/responses", response_model=SurveyResponseDetail, status_code=201)
def submit_survey_response(
    response_data: SurveyResponseCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: BrigadistaUser
):
    """
    Submit survey response (offline sync).
    
    Features:
    - Idempotent (uses client_id for deduplication)
    - Accepts responses completed offline
    - Validates against survey version
    """
    service = ResponseService(db)
    return service.submit_response(response_data, current_user.id)


@router.get("/responses/me", response_model=List[SurveyResponseDetail])
def get_my_responses(
    db: Annotated[Session, Depends(get_db)],
    current_user: BrigadistaUser,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    Get current user's submitted responses.
    """
    service = ResponseService(db)
    return service.get_user_responses(current_user.id, skip=skip, limit=limit)
