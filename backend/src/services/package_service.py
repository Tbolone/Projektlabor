from datetime import date, datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import String, cast
from sqlalchemy.orm import Session, joinedload

from src.models.models import (
    Contact,
    Courier,
    Package,
    PackageEvent,
    PackageStatus,
    User,
)

STARTED_STATUSES = {
    PackageStatus.OUT_FOR_PICKUP,
    PackageStatus.PICKED_UP,
    PackageStatus.IN_WAREHOUSE,
    PackageStatus.ASSIGNED_FOR_DELIVERY,
    PackageStatus.OUT_FOR_DELIVERY,
    PackageStatus.DELIVERED,
}

FINAL_STATUSES = {
    PackageStatus.DELIVERED,
    PackageStatus.RETURNED_TO_SENDER,
    PackageStatus.CANCELLED,
}

ALLOWED_TRANSITIONS: dict[PackageStatus, set[PackageStatus]] = {
    PackageStatus.CREATED: {
        PackageStatus.READY_FOR_PICKUP,
        PackageStatus.ASSIGNED_FOR_PICKUP,
        PackageStatus.CANCELLED,
    },
    PackageStatus.READY_FOR_PICKUP: {
        PackageStatus.ASSIGNED_FOR_PICKUP,
        PackageStatus.CANCELLED,
    },
    PackageStatus.ASSIGNED_FOR_PICKUP: {
        PackageStatus.OUT_FOR_PICKUP,
        PackageStatus.READY_FOR_PICKUP,
        PackageStatus.CANCELLED,
    },
    PackageStatus.OUT_FOR_PICKUP: {
        PackageStatus.PICKED_UP,
        PackageStatus.FAILED_DELIVERY,
    },
    PackageStatus.PICKED_UP: {
        PackageStatus.IN_WAREHOUSE,
    },
    PackageStatus.IN_WAREHOUSE: {
        PackageStatus.ASSIGNED_FOR_DELIVERY,
    },
    PackageStatus.ASSIGNED_FOR_DELIVERY: {
        PackageStatus.OUT_FOR_DELIVERY,
        PackageStatus.IN_WAREHOUSE,
    },
    PackageStatus.OUT_FOR_DELIVERY: {
        PackageStatus.DELIVERED,
        PackageStatus.FAILED_DELIVERY,
    },
    PackageStatus.FAILED_DELIVERY: {
        PackageStatus.IN_WAREHOUSE,
        PackageStatus.RETURNED_TO_SENDER,
    },
    PackageStatus.DELIVERED: set(),
    PackageStatus.RETURNED_TO_SENDER: set(),
    PackageStatus.CANCELLED: set(),
}


def _base_query(db: Session):
    return (
        db.query(Package)
        .options(
            joinedload(Package.pickup_contact),
            joinedload(Package.delivery_contact),
            joinedload(Package.pickup_courier).joinedload(Courier.user),
            joinedload(Package.delivery_courier).joinedload(Courier.user),
        )
    )


def get_package(db: Session, package_id: int) -> Package:
    package = _base_query(db).filter(Package.id == package_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="A csomag nem található")
    return package


def get_package_by_tracking_id(db: Session, tracking_id: str) -> Package:
    package = _base_query(db).filter(Package.tracking_id == tracking_id).first()
    if not package:
        raise HTTPException(status_code=404, detail="Nincs csomag ezzel az azonosítóval")
    return package


def list_packages(
    db: Session,
    *,
    status_filter: PackageStatus | None = None,
    courier_id: int | None = None,
    search: str | None = None,
) -> list[Package]:
    query = _base_query(db)

    if status_filter:
        query = query.filter(Package.current_status == status_filter)

    if courier_id:
        query = query.filter(
            (Package.pickup_courier_id == courier_id)
            | (Package.delivery_courier_id == courier_id)
        )

    if search:
        pattern = f"%{search.strip()}%"
        query = query.join(
            Contact, Package.delivery_contact_id == Contact.id
        ).filter(
            Contact.name.ilike(pattern)
            | Contact.city.ilike(pattern)
            | cast(Package.tracking_id, String).ilike(pattern)
        )

    return query.order_by(Package.id.desc()).all()


def add_event(
    db: Session,
    package: Package,
    actor: User,
    new_status: PackageStatus,
    comment: str | None = None,
    courier: Courier | None = None,
) -> PackageEvent:
    event = PackageEvent(
        package_id=package.id,
        actor_id=actor.user_id,
        courier_id=courier.id if courier else None,
        status=new_status,
        comment=comment,
        timestamp=datetime.now(timezone.utc),
    )
    package.current_status = new_status
    db.add(event)
    return event


def ensure_transition(package: Package, new_status: PackageStatus) -> None:
    if package.current_status == new_status:
        return

    allowed = ALLOWED_TRANSITIONS.get(package.current_status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Ebből az állapotból ({package.current_status.value}) nem lehet "
                f"a(z) {new_status.value} állapotba lépni"
            ),
        )


def is_started(package: Package) -> bool:
    return package.current_status in STARTED_STATUSES


def assign_courier(
    db: Session,
    package: Package,
    courier: Courier,
    stage: str,
    actor: User,
    *,
    allow_after_start: bool = False,
) -> Package:
    if package.current_status in FINAL_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lezárt csomaghoz nem lehet futárt rendelni",
        )

    if stage == "pickup":
        if package.current_status in STARTED_STATUSES and not allow_after_start:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A futár már elindult, a felvételi hozzárendelés nem módosítható",
            )

        package.pickup_courier_id = courier.id
        if package.current_status in (
            PackageStatus.CREATED,
            PackageStatus.READY_FOR_PICKUP,
            PackageStatus.ASSIGNED_FOR_PICKUP,
        ):
            add_event(
                db, package, actor, PackageStatus.ASSIGNED_FOR_PICKUP,
                comment=f"Felvételre kijelölt futár: {courier.user.name}",
                courier=courier,
            )

    else:
        if package.current_status == PackageStatus.OUT_FOR_DELIVERY and not allow_after_start:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A futár már úton van, a kiszállítási hozzárendelés nem módosítható",
            )

        if package.current_status not in (
            PackageStatus.IN_WAREHOUSE,
            PackageStatus.ASSIGNED_FOR_DELIVERY,
            PackageStatus.OUT_FOR_DELIVERY,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Kiszállításra csak raktárban lévő csomag jelölhető ki",
            )

        package.delivery_courier_id = courier.id
        if package.current_status == PackageStatus.IN_WAREHOUSE:
            add_event(
                db, package, actor, PackageStatus.ASSIGNED_FOR_DELIVERY,
                comment=f"Kiszállításra kijelölt futár: {courier.user.name}",
                courier=courier,
            )

    db.commit()
    db.refresh(package)
    return package


def change_status(
    db: Session,
    package: Package,
    new_status: PackageStatus,
    actor: User,
    comment: str | None = None,
    courier: Courier | None = None,
) -> Package:
    ensure_transition(package, new_status)
    add_event(db, package, actor, new_status, comment=comment, courier=courier)
    db.commit()
    db.refresh(package)
    return package


def can_customer_modify(package: Package) -> bool:
    if package.current_status not in (
        PackageStatus.CREATED,
        PackageStatus.READY_FOR_PICKUP,
        PackageStatus.ASSIGNED_FOR_PICKUP,
    ):
        return False
    return date.today() < package.pickup_date


def create_package(db: Session, data, actor: User) -> Package:
    pickup_contact = Contact(**data.pickup_contact.model_dump())
    delivery_contact = Contact(**data.delivery_contact.model_dump())
    db.add(pickup_contact)
    db.add(delivery_contact)
    db.flush()

    package = Package(
        pickup_contact_id=pickup_contact.id,
        delivery_contact_id=delivery_contact.id,
        sender_id=data.sender_id,
        receiver_id=data.receiver_id,
        size=data.size,
        weight=data.weight,
        pickup_date=data.pickup_date,
        pickup_time_slot=data.pickup_time_slot,
        delivery_date=data.delivery_date,
        delivery_time_slot=data.delivery_time_slot,
        current_status=PackageStatus.CREATED,
    )
    db.add(package)
    db.flush()

    add_event(db, package, actor, PackageStatus.CREATED, comment="Csomag előjegyezve")
    db.commit()
    db.refresh(package)
    return package


def update_package(db: Session, package: Package, data, actor: User) -> Package:
    payload = data.model_dump(exclude_unset=True)

    new_status = payload.pop("current_status", None)
    pickup_contact = payload.pop("pickup_contact", None)
    delivery_contact = payload.pop("delivery_contact", None)

    for field, value in payload.items():
        setattr(package, field, value)

    if pickup_contact:
        for field, value in pickup_contact.items():
            setattr(package.pickup_contact, field, value)

    if delivery_contact:
        for field, value in delivery_contact.items():
            setattr(package.delivery_contact, field, value)

    if new_status and new_status != package.current_status:
        add_event(
            db, package, actor, new_status,
            comment="Státusz módosítva adminisztrátor által",
        )

    db.commit()
    db.refresh(package)
    return package


def delete_package(db: Session, package: Package) -> None:
    db.delete(package)
    db.commit()
