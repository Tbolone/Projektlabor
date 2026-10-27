from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from src.models.models import Courier, Package, PackageEvent, PackageStatus, User, UserType
from src.services import package_service

PICKUP_ACTIVE = {PackageStatus.ASSIGNED_FOR_PICKUP, PackageStatus.OUT_FOR_PICKUP}
DELIVERY_ACTIVE = {PackageStatus.ASSIGNED_FOR_DELIVERY, PackageStatus.OUT_FOR_DELIVERY}


def list_couriers(db: Session) -> list[Courier]:
    return (
        db.query(Courier)
        .options(joinedload(Courier.user))
        .join(User, Courier.user_id == User.user_id)
        .order_by(User.name)
        .all()
    )


def get_courier(db: Session, courier_id: int) -> Courier:
    courier = (
        db.query(Courier)
        .options(joinedload(Courier.user))
        .filter(Courier.id == courier_id)
        .first()
    )
    if not courier:
        raise HTTPException(status_code=404, detail="A futár nem található")
    return courier


def active_packages(db: Session, courier: Courier) -> list[Package]:
    return (
        package_service._base_query(db)
        .filter(
            (
                (Package.pickup_courier_id == courier.id)
                & Package.current_status.in_(PICKUP_ACTIVE)
            )
            | (
                (Package.delivery_courier_id == courier.id)
                & Package.current_status.in_(DELIVERY_ACTIVE)
            )
        )
        .order_by(Package.pickup_date, Package.id)
        .all()
    )


def courier_load(db: Session, courier: Courier) -> tuple[int, float]:
    packages = active_packages(db, courier)
    return len(packages), round(sum(p.weight for p in packages), 2)


def ensure_assigned(package: Package, courier: Courier, stage: str) -> None:
    assigned_id = (
        package.pickup_courier_id if stage == "pickup" else package.delivery_courier_id
    )
    if assigned_id != courier.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ez a csomag nincs hozzád rendelve",
        )


def history(db: Session, courier: Courier, period: str) -> list[dict]:
    if period not in ("day", "week", "month"):
        raise HTTPException(status_code=422, detail="A bontás csak day, week vagy month lehet")

    events = (
        db.query(PackageEvent)
        .filter(
            PackageEvent.courier_id == courier.id,
            PackageEvent.status.in_([PackageStatus.DELIVERED, PackageStatus.PICKED_UP]),
        )
        .order_by(PackageEvent.timestamp.desc())
        .all()
    )

    buckets: dict[str, dict] = {}
    for event in events:
        stamp = event.timestamp
        if period == "day":
            key = stamp.strftime("%Y-%m-%d")
        elif period == "week":
            iso = stamp.isocalendar()
            key = f"{iso.year}. {iso.week}. hét"
        else:
            key = stamp.strftime("%Y-%m")

        bucket = buckets.setdefault(key, {"period": key, "delivered": 0, "picked_up": 0})
        if event.status == PackageStatus.DELIVERED:
            bucket["delivered"] += 1
        else:
            bucket["picked_up"] += 1

    return sorted(buckets.values(), key=lambda b: b["period"], reverse=True)


def create_courier(db: Session, data, hash_password) -> Courier:
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ez az email cím már foglalt")

    user = User(
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        type=UserType.DELIVERY_MAN,
    )
    db.add(user)
    db.flush()

    courier = Courier(
        user_id=user.user_id,
        is_available=data.is_available,
        max_capacity=data.max_capacity,
        vehicle_plate_number=data.vehicle_plate_number,
    )
    db.add(courier)
    db.commit()
    db.refresh(courier)
    return courier


def update_courier(db: Session, courier: Courier, data, hash_password) -> Courier:
    payload = data.model_dump(exclude_unset=True)

    name = payload.pop("name", None)
    email = payload.pop("email", None)
    password = payload.pop("password", None)

    if email and email != courier.user.email:
        clash = db.query(User).filter(User.email == email).first()
        if clash:
            raise HTTPException(status_code=409, detail="Ez az email cím már foglalt")
        courier.user.email = email

    if name:
        courier.user.name = name

    if password:
        courier.user.password_hash = hash_password(password)

    for field, value in payload.items():
        setattr(courier, field, value)

    db.commit()
    db.refresh(courier)
    return courier


def delete_courier(db: Session, courier: Courier) -> None:
    count, _ = courier_load(db, courier)
    if count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A futárhoz még {count} aktív csomag tartozik",
        )

    user = courier.user
    db.delete(courier)
    if user:
        db.delete(user)
    db.commit()
