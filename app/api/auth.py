"""Authentication router."""
from typing import Annotated
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.schemas.user import LoginResponse, UserResponse
from app.api.dependencies import get_current_user, AnyUser
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Login with email and password.
    
    Accepts FormData with:
    - username: user email
    - password: user password
    
    Returns JWT access token with user data.
    """
    auth_service = AuthService(db)
    # OAuth2PasswordRequestForm uses "username" field for email
    return auth_service.login(form_data.username, form_data.password)


@router.post("/logout")
def logout(current_user: AnyUser):
    """
    Logout current user.
    
    In a stateless JWT system, logout is handled client-side by removing the token.
    This endpoint exists for compatibility and could be extended to:
    - Add token to blacklist
    - Log logout event
    - Clear server-side sessions
    """
    # TODO: Add token to blacklist if implementing token revocation
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: AnyUser):
    """
    Get current authenticated user's information.
    
    Requires valid JWT token in Authorization header.
    """
    return current_user


@router.post("/refresh")
def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token.
    
    TODO: Implement refresh token logic:
    - Validate refresh token
    - Generate new access token
    - Return new token
    
    For now, returns error as refresh tokens are not fully implemented.
    """
    from fastapi import HTTPException, status
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token endpoint not yet implemented"
    )
