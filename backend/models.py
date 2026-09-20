import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class RoleEnum(enum.Enum):
    GUEST = "Guest"
    CUSTOMER = "Customer"
    COURIER = "Courier"
    LOGISTICS = "Logistics"
    ADMIN = "Admin"

class PackageStatus(enum.Enum):
    REGISTERED = "Registered"
    ASSIGNED_FOR_PICKUP = "Assigned_for_Pickup"
    PICKED_UP = "Picked_Up"
    IN_WAREHOUSE = "In_Warehouse"
    ASSIGNED_FOR_DELIVERY = "Assigned_for_Delivery"
    OUT_FOR_DELIVERY = "Out_for_Delivery"
    DELIVERED = "Delivered"
    FAILED = "Failed"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.CUSTOMER, nullable=False)

class Package(Base):
    __tablename__ = "packages"
    id = Column(Integer, primary_key=True, index=True)
    tracking_code = Column(String, unique=True, index=True, nullable=False)
    
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Null, ha vendég
    recipient_email = Column(String, nullable=False)
    
    size = Column(String, nullable=False) # S, M, L, XL
    pickup_address = Column(String, nullable=False)
    delivery_address = Column(String, nullable=False)
    time_slot = Column(String, nullable=True)
    
    status = Column(Enum(PackageStatus), default=PackageStatus.REGISTERED, nullable=False)
    
    pickup_courier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    delivery_courier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

    # Kapcsolatok a User táblához
    sender = relationship("User", foreign_keys=[sender_id])
    pickup_courier = relationship("User", foreign_keys=[pickup_courier_id])
    delivery_courier = relationship("User", foreign_keys=[delivery_courier_id])