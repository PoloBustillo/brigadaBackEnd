"""Authentication service."""
from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import Token


class AuthService:
    """Authentication business logic."""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user by email and password.
        
        Returns:
            User if authentication successful, None otherwise
        """
        user = self.user_repo.get_by_email(email)
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def login(self, email: str, password: str) -> Token:
        """
        Login user and return JWT token.
        
        Raises:
            HTTPException: If authentication fails
        """
        user = self.authenticate_user(email, password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value},
            expires_delta=access_token_expires
        )
        
        return Token(access_token=access_token)
