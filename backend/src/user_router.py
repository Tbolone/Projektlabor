from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_db
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from services import user_service
from typing import Annotated

from deps import get_current_user

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/", response_model=list[UserResponse], status_code=200)
def get_user_list(current_user: Annotated[User, Depends(get_current_user)], db: Session = Depends(get_db)):
    user_service.get_user_list(db)
    return user_service.get_user_list(db)

