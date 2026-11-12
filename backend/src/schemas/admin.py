from pydantic import BaseModel, EmailStr, Field, field_validator

from models.models import UserType


class AdminUserResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    type: UserType
    primary_address: str | None = None

    model_config = {"from_attributes": True}


class UserCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=4, max_length=72)
    type: UserType
    primary_address: str | None = Field(default=None, max_length=255)


class UserUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=4, max_length=72)
    type: UserType | None = None
    primary_address: str | None = Field(default=None, max_length=255)

    @field_validator("primary_address")
    @classmethod
    def empty_address_to_none(cls, value):
        """Üresen hagyott lakcím törlést jelent, nem üres szöveget."""
        return value or None
