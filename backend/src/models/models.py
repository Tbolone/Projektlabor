import enum
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    String,
    UUID,
    func,
    Text,
    Boolean
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.db import Base


class UserType(str, enum.Enum):
    REGISTERED_CUSTOMER = "registered customer"
    UNREGISTERED_CUSTOMER = "unregistered customer"
    ADMIN = "admin"
    WAREHOUSE_STAFF = "warehouse_staff"
    DELIVERY_MAN = "delivery_man"

class PackageStatus(str, enum.Enum):
    CREATED = "created"
    READY_FOR_PICKUP = "ready_for_pickup"
    ASSIGNED_FOR_PICKUP = "assigned_for_pickup"
    OUT_FOR_PICKUP = "out_for_pickup"
    PICKED_UP = "picked_up"
    IN_WAREHOUSE = "in_warehouse"
    ASSIGNED_FOR_DELIVERY = "assigned_for_delivery"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"

    FAILED_DELIVERY = "failed_delivery"
    RETURNED_TO_SENDER = "returned_to_sender"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    type: Mapped[UserType] = mapped_column(
        Enum(UserType, name="user_type_enum"),
        nullable=False,
        default=UserType.UNREGISTERED_CUSTOMER
    )

class Package(Base):
    __tablename__ = "packages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tracking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True
    )

    pickup_contact_id: Mapped[int] = mapped_column(
        ForeignKey("contacts.id"), nullable=False
    )
    delivery_contact_id: Mapped[int] = mapped_column(
        ForeignKey("contacts.id"), nullable=False
    )

    sender_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.user_id"), nullable=True
    )
    receiver_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.user_id"), nullable=True
    )

    size: Mapped[str] = mapped_column(String(50), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)

    pickup_date: Mapped[date] = mapped_column(Date, nullable=False)
    pickup_time_slot: Mapped[str] = mapped_column(String(50), nullable=False)
    delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    delivery_time_slot: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    current_status: Mapped[PackageStatus] = mapped_column(
        Enum(PackageStatus, name="package_status_enum"),
        nullable=False,
        default=PackageStatus.CREATED,
    )


    pickup_contact: Mapped["Contact"] = relationship(
        "Contact", foreign_keys=[pickup_contact_id]
    )
    delivery_contact: Mapped["Contact"] = relationship(
        "Contact", foreign_keys=[delivery_contact_id]
    )
    sender: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[sender_id]
    )
    receiver: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[receiver_id]
    )
    events: Mapped[list["PackageEvent"]] = relationship(
        "PackageEvent", back_populates="package", cascade="all, delete-orphan"
    )


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(20), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    street_address: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PackageEvent(Base):
    __tablename__ = "package_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    package_id: Mapped[int] = mapped_column(
        ForeignKey("packages.id", ondelete="CASCADE"), nullable=False, index=True
    )

    actor_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id"), nullable=False
    )

    courier_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("couriers.id"), nullable=True, index=True
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    status: Mapped[PackageStatus] = mapped_column(
        Enum(PackageStatus, name="package_status_enum"),
        nullable=False
    )

    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    package: Mapped["Package"] = relationship("Package", back_populates="events")
    actor: Mapped["User"] = relationship("User", foreign_keys=[actor_id])
    courier: Mapped[Optional["Courier"]] = relationship("Courier", foreign_keys=[courier_id])


class Courier(Base):
    __tablename__ = "couriers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False
    )

    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    max_capacity: Mapped[float] = mapped_column(Float, nullable=False)

    vehicle_plate_number: Mapped[str] = mapped_column(String(20), nullable=False)

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    events: Mapped[list["PackageEvent"]] = relationship("PackageEvent", back_populates="courier")
