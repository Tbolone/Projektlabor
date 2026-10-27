from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.deps import get_current_user, require_admin
from src.models.models import User
from src.schemas.auth import UserResponse
from src.services import user_service

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("/", response_model=list[UserResponse], status_code=200)
def get_user_list(
    current_user: Annotated[User, Depends(require_admin)],
    db: Session = Depends(get_db),
):
    return user_service.get_user_list(db)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
