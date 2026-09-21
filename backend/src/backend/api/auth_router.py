from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database.db import get_db
from backend.schemas.auth import LoginRequest, TokenResponse
from backend.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """A frontend ide küldi a kérést."""
    # A Router csak továbbítja az adatokat a Service-nek
    token = auth_service.authenticate_user(db, request.email, request.password)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hibás email vagy jelszó"
        )
        
    # A Router visszaküldi a választ a frontendnek
    return TokenResponse(access_token=token)