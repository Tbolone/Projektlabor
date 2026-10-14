from pydantic import BaseModel, EmailStr, Field
from src.models.models import UserType


class UserResponse(BaseModel):
    id : int 
    name : str
    email : EmailStr
    type : UserType