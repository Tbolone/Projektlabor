from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.deps import get_current_courier, get_current_user
from src.models.models import Courier, PackageStatus, User
from src.schemas.courier import AvailabilityRequest, CourierResponse
from src.schemas.package import (
    PackageDetailResponse,
    PackageResponse,
    StatusChangeRequest,
)
from src.schemas.stats import DailyCount
from src.services import courier_service, package_service

router = APIRouter(prefix="/api/courier", tags=["Courier"])

CurrentCourier = Annotated[Courier, Depends(get_current_courier)]
CurrentUser = Annotated[User, Depends(get_current_user)]
Db = Annotated[Session, Depends(get_db)]


def _to_response(db: Session, courier: Courier) -> CourierResponse:
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


@router.get("/me", response_model=CourierResponse)
def get_my_profile(courier: CurrentCourier, db: Db):
    return _to_response(db, courier)


@router.patch("/me/availability", response_model=CourierResponse)
def set_availability(request: AvailabilityRequest, courier: CurrentCourier, db: Db):
    courier.is_available = request.is_available
    db.commit()
    db.refresh(courier)
    return _to_response(db, courier)


@router.get("/tasks", response_model=list[PackageResponse])
def get_my_tasks(courier: CurrentCourier, db: Db):
    return courier_service.active_packages(db, courier)


@router.get("/packages/{package_id}", response_model=PackageDetailResponse)
def get_package_detail(package_id: int, courier: CurrentCourier, db: Db):
    package = package_service.get_package(db, package_id)
    return _package_with_events(db, package)


@router.post("/packages/{package_id}/start-pickup", response_model=PackageResponse)
def start_pickup(
    package_id: int,
    request: StatusChangeRequest,
    courier: CurrentCourier,
    user: CurrentUser,
    db: Db,
):
    package = package_service.get_package(db, package_id)
    courier_service.ensure_assigned(package, courier, "pickup")
    return package_service.change_status(
        db, package, PackageStatus.OUT_FOR_PICKUP, user, request.comment, courier
    )


@router.post("/packages/{package_id}/pickup", response_model=PackageResponse)
def confirm_pickup(
    package_id: int,
    request: StatusChangeRequest,
    courier: CurrentCourier,
    user: CurrentUser,
    db: Db,
):
    package = package_service.get_package(db, package_id)
    courier_service.ensure_assigned(package, courier, "pickup")
    return package_service.change_status(
        db, package, PackageStatus.PICKED_UP, user, request.comment, courier
    )


@router.post("/packages/{package_id}/deliver-to-warehouse", response_model=PackageResponse)
def deliver_to_warehouse(
    package_id: int,
    request: StatusChangeRequest,
    courier: CurrentCourier,
    user: CurrentUser,
    db: Db,
):
    package = package_service.get_package(db, package_id)
    courier_service.ensure_assigned(package, courier, "pickup")
    return package_service.change_status(
        db, package, PackageStatus.IN_WAREHOUSE, user, request.comment, courier
    )


@router.post("/packages/{package_id}/start-delivery", response_model=PackageResponse)
def start_delivery(
    package_id: int,
    request: StatusChangeRequest,
    courier: CurrentCourier,
    user: CurrentUser,
    db: Db,
):
    package = package_service.get_package(db, package_id)
    courier_service.ensure_assigned(package, courier, "delivery")
    return package_service.change_status(
        db, package, PackageStatus.OUT_FOR_DELIVERY, user, request.comment, courier
    )


@router.post("/packages/{package_id}/deliver", response_model=PackageResponse)
def confirm_delivery(
    package_id: int,
    request: StatusChangeRequest,
    courier: CurrentCourier,
    user: CurrentUser,
    db: Db,
):
    package = package_service.get_package(db, package_id)
    courier_service.ensure_assigned(package, courier, "delivery")
    return package_service.change_status(
        db, package, PackageStatus.DELIVERED, user, request.comment, courier
    )


@router.post("/packages/{package_id}/fail", response_model=PackageResponse)
def report_failure(
    package_id: int,
    request: StatusChangeRequest,
    courier: CurrentCourier,
    user: CurrentUser,
    db: Db,
):
    package = package_service.get_package(db, package_id)
    stage = "delivery" if package.delivery_courier_id == courier.id else "pickup"
    courier_service.ensure_assigned(package, courier, stage)
    return package_service.change_status(
        db, package, PackageStatus.FAILED_DELIVERY, user, request.comment, courier
    )


@router.get("/history", response_model=list[DailyCount])
def get_history(
    courier: CurrentCourier,
    db: Db,
    period: Annotated[str, Query(pattern="^(day|week|month)$")] = "day",
):
    return courier_service.history(db, courier, period)


def _package_with_events(db: Session, package):
    from src.models.models import PackageEvent

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
