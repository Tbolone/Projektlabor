from backend.src.models.models import User
from backend.src.schemas.user import PasswordChangeRequest, UserProfileResponse, UserProfileUpdateRequest
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

@router.get("/me", response_model=UserProfileResponse)
def get_my_profile(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
 
 
@router.put("/me", response_model=UserProfileResponse)
def update_my_profile(
    request: UserProfileUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    try:
        return user_service.update_profile(
            db, current_user.user_id, request.name, request.primary_address
        )
    except user_service.UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A felhasználó nem található.",
        ) from exc
 
 
@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    request: PasswordChangeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    try:
        user_service.change_password(
            db, current_user.user_id, request.current_password, request.new_password
        )
    except user_service.InvalidCurrentPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hibás jelenlegi jelszó.",
        ) from exc
    except user_service.UserNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="A felhasználó nem található.",
        ) from exc

