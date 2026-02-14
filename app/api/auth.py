"""Authentication router."""
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import UserLogin, Token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin,
    db: Annotated[Session, Depends(get_db)]
):
    """
    Login with email and password.
    
    Returns JWT access token.
    """
    auth_service = AuthService(db)
    return auth_service.login(credentials.email, credentials.password)
