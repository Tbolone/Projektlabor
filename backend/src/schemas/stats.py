from datetime import date

from pydantic import BaseModel


class WarehouseStats(BaseModel):
    in_warehouse: int
    waiting_for_pickup: int
    out_for_pickup: int
    out_for_delivery: int
    delivered_total: int
    failed_total: int


class WarehouseHistoryPoint(BaseModel):
    day: date
    arrived: int
    left: int
    closing_stock: int


class CourierStats(BaseModel):
    courier_id: int
    name: str
    vehicle_plate_number: str
    is_available: bool
    delivered_count: int
    picked_up_count: int
    failed_count: int
    active_count: int
    avg_delivery_hours: float | None = None
    packages_per_day: float | None = None


class DailyCount(BaseModel):
    period: str
    delivered: int
    picked_up: int


class AdminStatsResponse(BaseModel):
    warehouse: WarehouseStats
    warehouse_history: list[WarehouseHistoryPoint]
    couriers: list[CourierStats]
    total_packages: int
    avg_delivery_hours: float | None = None
    status_breakdown: dict[str, int]
