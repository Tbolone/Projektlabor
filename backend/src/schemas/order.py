from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import date

class ContactSchema(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    zip: str  # DB-ben zip_code
    city: str
    street: str  # DB-ben street_address

class PackageCreateSchema(BaseModel):
    size: str
    weight: float
    pickup_date: Optional[date] = None
    pickup_time_slot: str

class OrderCreateRequest(BaseModel):
    sender: ContactSchema
    receiver: ContactSchema
    package: PackageCreateSchema

class UserResponseSchema(BaseModel):
    user_id: int
    name: str
    email: str

    class Config:
        from_attributes = True

class ContactResponseSchema(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    zip_code: str
    city: str
    street_address: str

    class Config:
        from_attributes = True

class PackageResponseSchema(BaseModel):
    id: int
    tracking_id: UUID4
    size: str
    weight: float
    pickup_date: date
    pickup_time_slot: str
    current_status: str

    pickup_contact: Optional[ContactResponseSchema] = None
    delivery_contact: Optional[ContactResponseSchema] = None

    # Küldő és fogadó felhasználó (User) adatai
    sender: Optional[UserResponseSchema] = None
    receiver: Optional[UserResponseSchema] = None

    class Config:
        from_attributes = True