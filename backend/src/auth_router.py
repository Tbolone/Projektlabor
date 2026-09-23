from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_db
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from services import auth_service

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

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Új felhasználó regisztrálása."""
    try:
        user = auth_service.register_user(
            db, request.email, request.name, request.password
        )
    except auth_service.EmailAlreadyUsedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ez az email cím már regisztrálva van"
        )

    return user
