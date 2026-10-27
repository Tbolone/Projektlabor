import uuid
from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from src.models.models import PackageStatus


class ContactBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    zip_code: str = Field(min_length=1, max_length=20)
    city: str = Field(min_length=1, max_length=100)
    street_address: str = Field(min_length=1, max_length=255)
    email: EmailStr
    phone: str = Field(min_length=1, max_length=30)
    comment: str | None = None


class ContactResponse(ContactBase):
    id: int

    model_config = {"from_attributes": True}


class CourierBrief(BaseModel):
    id: int
    name: str
    vehicle_plate_number: str

    model_config = {"from_attributes": True}


class PackageEventResponse(BaseModel):
    id: int
    timestamp: datetime
    status: PackageStatus
    comment: str | None = None
    actor_name: str | None = None
    courier_name: str | None = None

    model_config = {"from_attributes": True}


class PackageResponse(BaseModel):
    id: int
    tracking_id: uuid.UUID
    current_status: PackageStatus

    size: str
    weight: float

    pickup_date: date
    pickup_time_slot: str
    delivery_date: date | None = None
    delivery_time_slot: str | None = None

    pickup_contact: ContactResponse
    delivery_contact: ContactResponse

    sender_id: int | None = None
    receiver_id: int | None = None

    pickup_courier: CourierBrief | None = None
    delivery_courier: CourierBrief | None = None

    model_config = {"from_attributes": True}


class PackageDetailResponse(PackageResponse):
    events: list[PackageEventResponse] = []


class PackageCreateRequest(BaseModel):
    pickup_contact: ContactBase
    delivery_contact: ContactBase
    size: str = Field(min_length=1, max_length=50)
    weight: float = Field(gt=0, le=1000)
    pickup_date: date
    pickup_time_slot: str = Field(min_length=1, max_length=50)
    delivery_date: date | None = None
    delivery_time_slot: str | None = Field(default=None, max_length=50)
    sender_id: int | None = None
    receiver_id: int | None = None


class PackageUpdateRequest(BaseModel):
    size: str | None = Field(default=None, min_length=1, max_length=50)
    weight: float | None = Field(default=None, gt=0, le=1000)
    pickup_date: date | None = None
    pickup_time_slot: str | None = Field(default=None, max_length=50)
    delivery_date: date | None = None
    delivery_time_slot: str | None = Field(default=None, max_length=50)
    current_status: PackageStatus | None = None
    pickup_contact: ContactBase | None = None
    delivery_contact: ContactBase | None = None


class AssignCourierRequest(BaseModel):
    courier_id: int
    stage: str = Field(pattern="^(pickup|delivery)$")


class StatusChangeRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=500)
