from pydantic import BaseModel
from typing import Optional
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