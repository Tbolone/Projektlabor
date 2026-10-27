from pydantic import BaseModel, EmailStr, Field

from src.models.models import UserType


class UserResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    type: UserType

    model_config = {"from_attributes": True}


class UserCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=4, max_length=72)
    type: UserType


class UserUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=4, max_length=72)
    type: UserType | None = None
