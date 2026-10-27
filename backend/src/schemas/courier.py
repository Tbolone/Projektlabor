from pydantic import BaseModel, EmailStr, Field

from src.models.models import UserType


class CourierResponse(BaseModel):
    id: int
    user_id: int
    name: str
    email: EmailStr
    is_available: bool
    max_capacity: float
    vehicle_plate_number: str

    active_package_count: int = 0
    current_load: float = 0.0

    model_config = {"from_attributes": True}


class CourierCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=4, max_length=72)
    max_capacity: float = Field(gt=0, le=10000)
    vehicle_plate_number: str = Field(min_length=1, max_length=20)
    is_available: bool = True


class CourierUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=4, max_length=72)
    max_capacity: float | None = Field(default=None, gt=0, le=10000)
    vehicle_plate_number: str | None = Field(default=None, min_length=1, max_length=20)
    is_available: bool | None = None


class AvailabilityRequest(BaseModel):
    is_available: bool
