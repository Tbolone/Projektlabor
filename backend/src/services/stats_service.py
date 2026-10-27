from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy.orm import Session, joinedload

from src.models.models import Courier, Package, PackageEvent, PackageStatus, User


def warehouse_snapshot(db: Session) -> dict:
    counts = defaultdict(int)
    for (current_status,) in db.query(Package.current_status).all():
        counts[current_status] += 1

    return {
        "in_warehouse": counts[PackageStatus.IN_WAREHOUSE]
        + counts[PackageStatus.ASSIGNED_FOR_DELIVERY],
        "waiting_for_pickup": counts[PackageStatus.CREATED]
        + counts[PackageStatus.READY_FOR_PICKUP]
        + counts[PackageStatus.ASSIGNED_FOR_PICKUP],
        "out_for_pickup": counts[PackageStatus.OUT_FOR_PICKUP],
        "out_for_delivery": counts[PackageStatus.OUT_FOR_DELIVERY],
        "delivered_total": counts[PackageStatus.DELIVERED],
        "failed_total": counts[PackageStatus.FAILED_DELIVERY]
        + counts[PackageStatus.RETURNED_TO_SENDER],
    }


def warehouse_history(db: Session, days: int = 14) -> list[dict]:
    today = date.today()
    start = today - timedelta(days=days - 1)

    arrivals = defaultdict(int)
    departures = defaultdict(int)

    events = (
        db.query(PackageEvent)
        .filter(PackageEvent.status.in_([PackageStatus.IN_WAREHOUSE, PackageStatus.OUT_FOR_DELIVERY]))
        .all()
    )
    for event in events:
        day = event.timestamp.date()
        if event.status == PackageStatus.IN_WAREHOUSE:
            arrivals[day] += 1
        else:
            departures[day] += 1

    snapshot = warehouse_snapshot(db)
    closing = snapshot["in_warehouse"]

    rows: list[dict] = []
    for offset in range(days):
        day = today - timedelta(days=offset)
        rows.append(
            {
                "day": day,
                "arrived": arrivals.get(day, 0),
                "left": departures.get(day, 0),
                "closing_stock": max(closing, 0),
            }
        )
        closing = closing - arrivals.get(day, 0) + departures.get(day, 0)

    rows.reverse()
    return [row for row in rows if row["day"] >= start]


def _delivery_durations(db: Session) -> dict[int, float]:
    events = (
        db.query(PackageEvent)
        .filter(PackageEvent.status.in_([PackageStatus.PICKED_UP, PackageStatus.DELIVERED]))
        .order_by(PackageEvent.timestamp)
        .all()
    )

    picked: dict[int, object] = {}
    durations: dict[int, float] = {}
    for event in events:
        if event.status == PackageStatus.PICKED_UP:
            picked[event.package_id] = event.timestamp
        elif event.package_id in picked:
            delta = event.timestamp - picked[event.package_id]
            durations[event.package_id] = delta.total_seconds() / 3600

    return durations


def courier_stats(db: Session) -> list[dict]:
    couriers = (
        db.query(Courier).options(joinedload(Courier.user)).all()
    )
    durations = _delivery_durations(db)

    rows = []
    for courier in couriers:
        events = (
            db.query(PackageEvent)
            .filter(PackageEvent.courier_id == courier.id)
            .all()
        )

        delivered = [e for e in events if e.status == PackageStatus.DELIVERED]
        picked_up = [e for e in events if e.status == PackageStatus.PICKED_UP]
        failed = [e for e in events if e.status == PackageStatus.FAILED_DELIVERY]

        active = (
            db.query(Package)
            .filter(
                (
                    (Package.pickup_courier_id == courier.id)
                    & Package.current_status.in_(
                        [PackageStatus.ASSIGNED_FOR_PICKUP, PackageStatus.OUT_FOR_PICKUP]
                    )
                )
                | (
                    (Package.delivery_courier_id == courier.id)
                    & Package.current_status.in_(
                        [PackageStatus.ASSIGNED_FOR_DELIVERY, PackageStatus.OUT_FOR_DELIVERY]
                    )
                )
            )
            .count()
        )

        own_durations = [
            durations[e.package_id] for e in delivered if e.package_id in durations
        ]
        avg_hours = round(sum(own_durations) / len(own_durations), 2) if own_durations else None

        active_days = {e.timestamp.date() for e in delivered}
        per_day = round(len(delivered) / len(active_days), 2) if active_days else None

        rows.append(
            {
                "courier_id": courier.id,
                "name": courier.user.name if courier.user else "—",
                "vehicle_plate_number": courier.vehicle_plate_number,
                "is_available": courier.is_available,
                "delivered_count": len(delivered),
                "picked_up_count": len(picked_up),
                "failed_count": len(failed),
                "active_count": active,
                "avg_delivery_hours": avg_hours,
                "packages_per_day": per_day,
            }
        )

    rows.sort(key=lambda r: r["delivered_count"], reverse=True)
    return rows


def admin_stats(db: Session) -> dict:
    durations = _delivery_durations(db)
    avg_hours = (
        round(sum(durations.values()) / len(durations), 2) if durations else None
    )

    breakdown = defaultdict(int)
    for (current_status,) in db.query(Package.current_status).all():
        breakdown[current_status.value] += 1

    return {
        "warehouse": warehouse_snapshot(db),
        "warehouse_history": warehouse_history(db),
        "couriers": courier_stats(db),
        "total_packages": db.query(Package).count(),
        "avg_delivery_hours": avg_hours,
        "status_breakdown": dict(breakdown),
    }
