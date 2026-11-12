from pydantic import BaseModel, EmailStr, Field
from models.models import UserType
from typing import Annotated
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
)


class UserResponse(BaseModel):
    id : int 
    name : str
    email : EmailStr
    type : UserType

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
 
    id: int = Field(validation_alias="user_id")
    name: str
    email: EmailStr
    primary_address: str | None = None
    type: UserType
 
 
class UserProfileUpdateRequest(BaseModel):
    name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
    ]
    primary_address: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)] | None
    ) = None
 
    @field_validator("primary_address")
    @classmethod
    def empty_address_to_none(cls, value):
        return value or None
 
 
class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=6)
 
    @field_validator("new_password")
    @classmethod
    def fits_bcrypt_limit(cls, value):
        if len(value.encode("utf-8")) > 72:
            raise ValueError("A jelszó legfeljebb 72 bájt hosszú lehet.")
        return value