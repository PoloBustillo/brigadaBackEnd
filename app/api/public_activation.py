"""Public Activation Endpoints (No Authentication Required)"""
from typing import Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.activation_service import ActivationCodeService
from app.schemas.activation import (
    ValidateCodeRequest,
    ValidateCodeResponse,
    CompleteActivationRequest,
    CompleteActivationResponse
)

router = APIRouter(prefix="/public/activate", tags=["Public - Activation"])


@router.post("/validate-code", response_model=ValidateCodeResponse)
def validate_activation_code(
    data: ValidateCodeRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Validate activation code and preview whitelist information.
    
    **Public endpoint** - No authentication required.
    
    Rate limit: 10 requests per minute per IP (enforced by middleware).
    
    Returns:
    - If valid: Whitelist entry info, expiration time, activation requirements
    - If invalid: Generic error message (for security)
    """
    service = ActivationCodeService(db)
    client_ip = request.client.host if request.client else "unknown"
    
    return service.validate_code(data, client_ip)


@router.post("/complete", response_model=CompleteActivationResponse)
async def complete_activation(
    data: CompleteActivationRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Complete user activation - creates user account.
    
    **Public endpoint** - No authentication required.
    
    Rate limit: 3 requests per hour per IP (enforced by middleware).
    
    Steps:
    1. Validates activation code
    2. Verifies identifier matches whitelist
    3. Creates user account with hashed password
    4. Marks code as used and whitelist as activated
    5. Returns access token for immediate login
    
    **Security Notes**:
    - Code is hashed and verified using bcrypt
    - Password is hashed using bcrypt
    - Failed attempts are logged for security monitoring
    - Code is locked after 5 failed validation attempts
    """
    service = ActivationCodeService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")
    device_id = request.headers.get("x-device-id")
    
    return await service.complete_activation(
        data,
        ip_address=client_ip,
        user_agent=user_agent,
        device_id=device_id
    )
