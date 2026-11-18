from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database.db import get_db
from deps import require_staff
from models.models import PackageStatus, User
from schemas.courier import CourierResponse
from schemas.package import (
    AssignCourierRequest,
    PackageDetailResponse,
    PackageResponse,
    StatusChangeRequest,
)
from services import courier_service, package_service

router = APIRouter(prefix="/api/warehouse", tags=["Warehouse"])

StaffUser = Annotated[User, Depends(require_staff)]
Db = Annotated[Session, Depends(get_db)]


@router.get("/packages", response_model=list[PackageResponse])
def list_packages(
    staff: StaffUser,
    db: Db,
    status_filter: Annotated[PackageStatus | None, Query(alias="status")] = None,
    courier_id: int | None = None,
    search: str | None = None,
):
    return package_service.list_packages(
        db, status_filter=status_filter, courier_id=courier_id, search=search
    )


@router.get("/packages/{package_id}", response_model=PackageDetailResponse)
def get_package(package_id: int, staff: StaffUser, db: Db):
    """Egy csomag részletei a teljes eseménytörténettel."""
    package = package_service.get_package(db, package_id)
    return package_service.with_events(db, package)


@router.post("/packages/{package_id}/receive", response_model=PackageResponse)
def receive_package(
    package_id: int, request: StatusChangeRequest, staff: StaffUser, db: Db
):
    """A raktáros felveszi a beérkezett csomagot a raktárba."""
    package = package_service.get_package(db, package_id)
    return package_service.change_status(
        db, package, PackageStatus.IN_WAREHOUSE, staff, request.comment
    )


@router.post("/packages/{package_id}/assign", response_model=PackageResponse)
def assign_courier(
    package_id: int, request: AssignCourierRequest, staff: StaffUser, db: Db
):
    """Futár kijelölése felvételre vagy kiszállításra.

    Ha a futár már elindult, a hozzárendelés nem módosítható (409).
    """
    package = package_service.get_package(db, package_id)
    courier = courier_service.get_courier(db, request.courier_id)
    return package_service.assign_courier(
        db, package, courier, request.stage, staff, allow_after_start=False
    )


@router.get("/couriers", response_model=list[CourierResponse])
def list_couriers(staff: StaffUser, db: Db):
    """Futárok a kiosztáshoz, aktuális terheltséggel."""
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
