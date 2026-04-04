"""
Admin dashboard endpoints backed by the SQL database.
"""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.routes import (
    public_demand_service as _demand_service,
    public_matching_service as _matching_service,
)
from backend.db.database import get_db
from backend.db.models import RideStatus
from backend.db.repositories import DriverRepository, RideRepository
from backend.services.ml_logging import load_match_outcomes_for_training

router = APIRouter(prefix="/admin", tags=["admin"])

PKT = ZoneInfo("Asia/Karachi")


class DriverAvailabilityRequest(BaseModel):
    available: bool


@router.get("/overview", summary="Return admin dashboard analytics")
async def admin_overview(db: AsyncSession = Depends(get_db)) -> dict:
    ride_repo = RideRepository(db)
    driver_repo = DriverRepository(db)

    rides = await ride_repo.get_all()
    drivers = await driver_repo.get_all()

    heatmap = _build_heatmap(rides)
    stats = _build_stats(rides, drivers, heatmap)
    revenue = {
        "day": _build_revenue_series(rides, period="day"),
        "week": _build_revenue_series(rides, period="week"),
        "month": _build_revenue_series(rides, period="month"),
    }

    return {
        "stats": stats,
        "revenue": revenue,
        "heatmap": heatmap,
        "drivers": [_serialize_driver(driver, rides) for driver in drivers],
        "rides": [_serialize_ride(ride) for ride in rides],
        "generated_at": datetime.now(tz=PKT).isoformat(),
    }


@router.patch(
    "/drivers/{driver_id}/availability",
    summary="Toggle driver availability from the admin dashboard",
)
async def update_driver_availability(
    driver_id: int,
    body: DriverAvailabilityRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    driver_repo = DriverRepository(db)

    updated = await driver_repo.update_availability(driver_id, available=body.available)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver '{driver_id}' not found.",
        )

    driver = await driver_repo.find_by_id(driver_id)
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver '{driver_id}' not found after update.",
        )

    ride_repo = RideRepository(db)
    rides = await ride_repo.get_driver_history(driver_id)
    return _serialize_driver(driver, rides)


@router.post("/ml/retrain", summary="Retrain AI models on real data")
async def retrain_models() -> dict:
    """
    Retrain both the demand forecast (XGBoost) and matching (Gradient Boosting)
    models using historical data from the database.
    """
    # 1. Demand forecast
    X, y = await _demand_service.generate_training_data()
    demand_trained = False
    if X is not None and y is not None:
        demand_trained = await asyncio.to_thread(_demand_service.train, X, y)

    # 2. Matching model
    outcomes = await load_match_outcomes_for_training(min_records=10)
    match_trained = False
    if outcomes:
        match_trained = await asyncio.to_thread(
            _matching_service.retrain_with_outcomes, outcomes
        )

    return {
        "demand_forecast_trained": demand_trained,
        "matching_model_trained": match_trained,
        "match_outcomes_used": len(outcomes),
        "generated_at": datetime.now(tz=PKT).isoformat(),
    }


@router.get("/ml/status", summary="Get AI model status")
async def ml_status() -> dict:
    """Return current training status and data counts for both AI models."""
    outcomes = await load_match_outcomes_for_training(min_records=0)
    return {
        "demand_forecast_ready": _demand_service._trained,
        "matching_model_ready": _matching_service._trained,
        "matching_model_real_data": _matching_service.is_trained_on_real_data,
        "match_outcomes_total": len(outcomes),
        "generated_at": datetime.now(tz=PKT).isoformat(),
    }


def _serialize_ride(ride) -> dict:
    return {
        "id": ride.id,
        "status": ride.status.value if hasattr(ride.status, "value") else str(ride.status),
        "rider_name": ride.rider.full_name if ride.rider else f"Rider #{ride.rider_id}",
        "driver_name": (
            ride.driver.user.full_name
            if ride.driver is not None and ride.driver.user is not None
            else "Unassigned"
        ),
        "fare_amount": _money_value(ride.payment.amount if ride.payment else ride.fare_amount),
        "surge_multiplier": ride.surge_multiplier,
        "distance_km": ride.distance_km,
        "pickup_address": ride.pickup_address,
        "dropoff_address": ride.dropoff_address,
        "pickup_lat": ride.pickup_lat,
        "pickup_lng": ride.pickup_lng,
        "dropoff_lat": ride.dropoff_lat,
        "dropoff_lng": ride.dropoff_lng,
        "requested_at": ride.requested_at.isoformat() if ride.requested_at else None,
        "matched_at": ride.matched_at.isoformat() if ride.matched_at else None,
        "completed_at": ride.completed_at.isoformat() if ride.completed_at else None,
    }


def _serialize_driver(driver, rides: list) -> dict:
    active_ride = next(
        (
            ride
            for ride in rides
            if ride.driver_id == driver.id
            if ride.status
            in {
                RideStatus.matched,
                RideStatus.en_route,
                RideStatus.arrived,
                RideStatus.in_progress,
            }
        ),
        None,
    )

    return {
        "id": driver.id,
        "user_id": driver.user_id,
        "name": driver.user.full_name if driver.user else f"Driver #{driver.id}",
        "phone": driver.user.phone if driver.user else None,
        "rating": driver.rating,
        "available": driver.available,
        "vehicle_type": driver.vehicle_type,
        "total_trips": driver.total_trips,
        "is_active": driver.is_active,
        "lat": driver.lat,
        "lng": driver.lng,
        "active_ride_id": active_ride.id if active_ride else None,
        "active_ride_status": (
            active_ride.status.value if active_ride and hasattr(active_ride.status, "value") else None
        ),
    }


def _build_stats(rides: list, drivers: list, heatmap: list[dict]) -> dict:
    completed_rides = [ride for ride in rides if ride.status == RideStatus.completed]
    active_rides = [
        ride
        for ride in rides
        if ride.status not in {RideStatus.completed, RideStatus.cancelled}
    ]
    total_revenue = round(sum(_ride_amount(ride) for ride in completed_rides), 2)
    avg_fare = round(
        total_revenue / len(completed_rides),
        2,
    ) if completed_rides else 0.0
    active_drivers = sum(1 for driver in drivers if driver.available and driver.is_active)
    online_drivers = sum(1 for driver in drivers if driver.is_active)
    surge_zones = sum(
        1 for point in heatmap if point["intensity"] >= 0.65 or point["avg_surge"] > 1.05
    )

    return {
        "total_rides": len(rides),
        "active_rides": len(active_rides),
        "completed_rides": len(completed_rides),
        "active_drivers": active_drivers,
        "online_drivers": online_drivers,
        "avg_fare": avg_fare,
        "total_revenue": total_revenue,
        "surge_zones": surge_zones,
    }


def _build_heatmap(rides: list) -> list[dict]:
    now = datetime.now(tz=PKT)
    recent_cutoff = now - timedelta(days=14)
    source_rides = [
        ride
        for ride in rides
        if ride.requested_at is not None
        and ride.requested_at.astimezone(PKT) >= recent_cutoff
    ] or rides

    buckets: dict[tuple[float, float], dict] = defaultdict(
        lambda: {"lat_sum": 0.0, "lng_sum": 0.0, "count": 0, "surge_sum": 0.0}
    )

    for ride in source_rides:
        key = (round(ride.pickup_lat, 2), round(ride.pickup_lng, 2))
        bucket = buckets[key]
        bucket["lat_sum"] += ride.pickup_lat
        bucket["lng_sum"] += ride.pickup_lng
        bucket["count"] += 1
        bucket["surge_sum"] += float(ride.surge_multiplier or 1.0)

    if not buckets:
        return []

    peak_count = max(bucket["count"] for bucket in buckets.values())
    points = []
    for bucket in sorted(buckets.values(), key=lambda item: item["count"], reverse=True)[:18]:
        points.append(
            {
                "lat": round(bucket["lat_sum"] / bucket["count"], 5),
                "lng": round(bucket["lng_sum"] / bucket["count"], 5),
                "intensity": round(bucket["count"] / peak_count, 2),
                "rides": bucket["count"],
                "avg_surge": round(bucket["surge_sum"] / bucket["count"], 2),
            }
        )

    return points


def _build_revenue_series(rides: list, *, period: str) -> list[dict]:
    now = datetime.now(tz=PKT)
    completed = [
        ride
        for ride in rides
        if ride.status == RideStatus.completed and _ride_amount(ride) > 0
    ]

    if period == "day":
        return _build_daily_series(completed, now)
    if period == "week":
        return _build_weekly_series(completed, now)
    if period == "month":
        return _build_monthly_series(completed, now)
    raise ValueError(f"Unsupported period '{period}'.")


def _build_daily_series(rides: list, now: datetime) -> list[dict]:
    values = {}
    for offset in range(6, -1, -1):
        day = (now - timedelta(days=offset)).date()
        values[day] = 0.0

    for ride in rides:
        day = _ride_revenue_time(ride).astimezone(PKT).date()
        if day in values:
            values[day] += _ride_amount(ride)

    return [
        {"label": day.strftime("%d %b"), "amount": round(amount, 2)}
        for day, amount in values.items()
    ]


def _build_weekly_series(rides: list, now: datetime) -> list[dict]:
    current_monday = now.date() - timedelta(days=now.weekday())
    values = {}
    for offset in range(7, -1, -1):
        week_start = current_monday - timedelta(weeks=offset)
        values[week_start] = 0.0

    for ride in rides:
        ride_day = _ride_revenue_time(ride).astimezone(PKT).date()
        week_start = ride_day - timedelta(days=ride_day.weekday())
        if week_start in values:
            values[week_start] += _ride_amount(ride)

    return [
        {"label": week_start.strftime("%d %b"), "amount": round(amount, 2)}
        for week_start, amount in values.items()
    ]


def _build_monthly_series(rides: list, now: datetime) -> list[dict]:
    keys: list[tuple[int, int]] = []
    year = now.year
    month = now.month
    for _ in range(6):
        keys.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    keys.reverse()

    values = {key: 0.0 for key in keys}
    for ride in rides:
        ride_time = _ride_revenue_time(ride).astimezone(PKT)
        key = (ride_time.year, ride_time.month)
        if key in values:
            values[key] += _ride_amount(ride)

    return [
        {
            "label": datetime(year=year, month=month, day=1, tzinfo=PKT).strftime("%b"),
            "amount": round(amount, 2),
        }
        for (year, month), amount in values.items()
    ]


def _ride_revenue_time(ride) -> datetime:
    return ride.payment.created_at if ride.payment and ride.payment.created_at else (
        ride.completed_at or ride.requested_at
    )


def _ride_amount(ride) -> float:
    if ride.payment is not None and ride.payment.amount is not None:
        return _money_value(ride.payment.amount)
    return _money_value(ride.fare_amount)


def _money_value(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return round(float(value), 2)
