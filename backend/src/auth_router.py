from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.db import get_db
from src.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from src.services import auth_service
from typing import Annotated
from fastapi import Depends
from src.deps import get_current_user
from src.models.models import User

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    token = auth_service.authenticate_user(db, request.email, request.password)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hibás email vagy jelszó"
        )

    return TokenResponse(access_token=token)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
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

@router.get("/current_user", response_model=UserResponse)
def get_current_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user
