from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.deps import require_admin
from src.models.models import Package, PackageEvent, PackageStatus, User, UserType
from src.schemas.courier import (
    CourierCreateRequest,
    CourierResponse,
    CourierUpdateRequest,
)
from src.schemas.package import (
    AssignCourierRequest,
    PackageCreateRequest,
    PackageDetailResponse,
    PackageResponse,
    PackageUpdateRequest,
)
from src.schemas.stats import AdminStatsResponse, CourierStats
from src.schemas.user import UserCreateRequest, UserResponse, UserUpdateRequest
from src.services import auth_service, courier_service, package_service, stats_service

router = APIRouter(prefix="/api/admin", tags=["Admin"])

AdminUser = Annotated[User, Depends(require_admin)]
Db = Annotated[Session, Depends(get_db)]


@router.get("/users", response_model=list[UserResponse])
def list_users(
    admin: AdminUser,
    db: Db,
    type: UserType | None = None,
    search: str | None = None,
):
    query = db.query(User)

    if type:
        query = query.filter(User.type == type)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(User.name.ilike(pattern) | User.email.ilike(pattern))

    return query.order_by(User.user_id).all()


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(request: UserCreateRequest, admin: AdminUser, db: Db):
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=409, detail="Ez az email cím már foglalt")

    user = User(
        name=request.name,
        email=request.email,
        password_hash=auth_service.hash_password(request.password),
        type=request.type,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, request: UserUpdateRequest, admin: AdminUser, db: Db):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="A felhasználó nem található")

    payload = request.model_dump(exclude_unset=True)
    password = payload.pop("password", None)
    email = payload.pop("email", None)

    if email and email != user.email:
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=409, detail="Ez az email cím már foglalt")
        user.email = email

    if password:
        user.password_hash = auth_service.hash_password(password)

    for field, value in payload.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, admin: AdminUser, db: Db):
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="A felhasználó nem található")

    if user.user_id == admin.user_id:
        raise HTTPException(status_code=409, detail="Saját magadat nem törölheted")

    db.delete(user)
    db.commit()


@router.get("/couriers", response_model=list[CourierResponse])
def list_couriers(admin: AdminUser, db: Db):
    rows = []
    for courier in courier_service.list_couriers(db):
        count, load = courier_service.courier_load(db, courier)
        rows.append(
            CourierResponse(
                id=courier.id,
                user_id=courier.user_id,
                name=courier.user.name,
                email=courier.user.email,
                is_available=courier.is_available,
                max_capacity=courier.max_capacity,
                vehicle_plate_number=courier.vehicle_plate_number,
                active_package_count=count,
                current_load=load,
            )
        )
    return rows


@router.post("/couriers", response_model=CourierResponse, status_code=status.HTTP_201_CREATED)
def create_courier(request: CourierCreateRequest, admin: AdminUser, db: Db):
    courier = courier_service.create_courier(db, request, auth_service.hash_password)
    return CourierResponse(
        id=courier.id,
        user_id=courier.user_id,
        name=courier.user.name,
        email=courier.user.email,
        is_available=courier.is_available,
        max_capacity=courier.max_capacity,
        vehicle_plate_number=courier.vehicle_plate_number,
    )


@router.patch("/couriers/{courier_id}", response_model=CourierResponse)
def update_courier(courier_id: int, request: CourierUpdateRequest, admin: AdminUser, db: Db):
    courier = courier_service.get_courier(db, courier_id)
    courier = courier_service.update_courier(db, courier, request, auth_service.hash_password)
    count, load = courier_service.courier_load(db, courier)
    return CourierResponse(
        id=courier.id,
        user_id=courier.user_id,
        name=courier.user.name,
        email=courier.user.email,
        is_available=courier.is_available,
        max_capacity=courier.max_capacity,
        vehicle_plate_number=courier.vehicle_plate_number,
        active_package_count=count,
        current_load=load,
    )


@router.delete("/couriers/{courier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_courier(courier_id: int, admin: AdminUser, db: Db):
    courier = courier_service.get_courier(db, courier_id)
    courier_service.delete_courier(db, courier)


@router.get("/packages", response_model=list[PackageResponse])
def list_packages(
    admin: AdminUser,
    db: Db,
    status_filter: Annotated[PackageStatus | None, Query(alias="status")] = None,
    courier_id: int | None = None,
    search: str | None = None,
):
    return package_service.list_packages(
        db, status_filter=status_filter, courier_id=courier_id, search=search
    )


@router.get("/packages/{package_id}", response_model=PackageDetailResponse)
def get_package(package_id: int, admin: AdminUser, db: Db):
    package = package_service.get_package(db, package_id)

    events = (
        db.query(PackageEvent)
        .filter(PackageEvent.package_id == package.id)
        .order_by(PackageEvent.timestamp.desc())
        .all()
    )

    detail = PackageDetailResponse.model_validate(package)
    detail.events = [
        {
            "id": event.id,
            "timestamp": event.timestamp,
            "status": event.status,
            "comment": event.comment,
            "actor_name": event.actor.name if event.actor else None,
            "courier_name": event.courier.user.name
            if event.courier and event.courier.user
            else None,
        }
        for event in events
    ]
    return detail


@router.post("/packages", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
def create_package(request: PackageCreateRequest, admin: AdminUser, db: Db):
    return package_service.create_package(db, request, admin)


@router.patch("/packages/{package_id}", response_model=PackageResponse)
def update_package(package_id: int, request: PackageUpdateRequest, admin: AdminUser, db: Db):
    package = package_service.get_package(db, package_id)
    return package_service.update_package(db, package, request, admin)


@router.delete("/packages/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(package_id: int, admin: AdminUser, db: Db):
    package = package_service.get_package(db, package_id)
    package_service.delete_package(db, package)


@router.post("/packages/{package_id}/assign", response_model=PackageResponse)
def assign_courier(
    package_id: int, request: AssignCourierRequest, admin: AdminUser, db: Db
):
    package = package_service.get_package(db, package_id)
    courier = courier_service.get_courier(db, request.courier_id)
    return package_service.assign_courier(
        db, package, courier, request.stage, admin, allow_after_start=True
    )


@router.get("/stats", response_model=AdminStatsResponse)
def get_stats(admin: AdminUser, db: Db):
    return stats_service.admin_stats(db)


@router.get("/stats/couriers", response_model=list[CourierStats])
def get_courier_stats(admin: AdminUser, db: Db):
    return stats_service.courier_stats(db)
