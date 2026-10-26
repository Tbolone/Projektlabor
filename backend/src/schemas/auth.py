from pydantic import BaseModel, EmailStr, Field
from src.models.models import UserType

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    # A bcrypt legfeljebb 72 bajtot kezel, ezert van felso hatar is.
    password: str = Field(min_length=6, max_length=72)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    user_id: int
    email: EmailStr
    name: str
    type: UserType

    model_config = {"from_attributes": True}
