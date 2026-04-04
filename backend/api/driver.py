"""
Driver application endpoints backed by the SQL database.
"""

import math
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.dependencies import require_driver
from backend.db.database import get_db
from backend.db.models import PaymentStatus, RideStatus
from backend.db.repositories import DriverRepository, PaymentRepository, RideRepository
from backend.services.pricing import DynamicPricingService

router = APIRouter(prefix="/driver", tags=["driver"])

PKT = ZoneInfo("Asia/Karachi")
_pricing_service = DynamicPricingService()

_STATUS_FLOW: dict[RideStatus, set[RideStatus]] = {
    RideStatus.matched: {RideStatus.en_route, RideStatus.in_progress},
    RideStatus.en_route: {RideStatus.arrived, RideStatus.in_progress},
    RideStatus.arrived: {RideStatus.in_progress},
    RideStatus.in_progress: {RideStatus.completed},
}


class DriverAvailabilityRequest(BaseModel):
    available: bool


class DriverLocationRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class DriverRideStatusRequest(BaseModel):
    status: str


@router.get("/dashboard", summary="Return the logged-in driver's dashboard")
async def driver_dashboard(
    current_user: dict = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
) -> dict:
    driver = await _load_driver_profile(db, int(current_user["sub"]))
    ride_repo = RideRepository(db)

    open_requests = await ride_repo.get_open_requests()
    active_ride = await ride_repo.get_driver_active_ride(driver.id)
    history = await ride_repo.get_driver_history(driver.id)

    return {
        "driver": _serialize_driver_profile(driver, history, active_ride),
        "incoming_requests": [
            _serialize_request(ride, driver.lat, driver.lng) for ride in open_requests[:8]
        ],
        "active_ride": _serialize_driver_ride(active_ride) if active_ride else None,
        "recent_completed": [
            _serialize_driver_ride(ride)
            for ride in history
            if ride.status == RideStatus.completed
        ][:5],
        "generated_at": datetime.now(tz=PKT).isoformat(),
    }


@router.patch("/availability", summary="Set driver online/offline availability")
async def update_driver_availability(
    body: DriverAvailabilityRequest,
    current_user: dict = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
) -> dict:
    driver = await _load_driver_profile(db, int(current_user["sub"]))
    driver_repo = DriverRepository(db)
    await driver_repo.update_availability(driver.id, available=body.available)

    refreshed = await driver_repo.find_by_id(driver.id)
    if refreshed is None:
        raise HTTPException(status_code=404, detail="Driver profile not found after update.")

    history = await RideRepository(db).get_driver_history(refreshed.id)
    active_ride = await RideRepository(db).get_driver_active_ride(refreshed.id)
    return _serialize_driver_profile(refreshed, history, active_ride)


@router.patch("/location", summary="Update the driver's current map location")
async def update_driver_location(
    body: DriverLocationRequest,
    current_user: dict = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
) -> dict:
    driver = await _load_driver_profile(db, int(current_user["sub"]))
    driver_repo = DriverRepository(db)
    await driver_repo.update_location(driver.id, lat=body.lat, lng=body.lng)

    refreshed = await driver_repo.find_by_id(driver.id)
    if refreshed is None:
        raise HTTPException(status_code=404, detail="Driver profile not found after location update.")

    history = await RideRepository(db).get_driver_history(refreshed.id)
    active_ride = await RideRepository(db).get_driver_active_ride(refreshed.id)
    return _serialize_driver_profile(refreshed, history, active_ride)


@router.post("/rides/{ride_id}/accept", summary="Accept an incoming ride request")
async def accept_ride(
    ride_id: int,
    current_user: dict = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
) -> dict:
    driver = await _load_driver_profile(db, int(current_user["sub"]))
    ride_repo = RideRepository(db)
    driver_repo = DriverRepository(db)

    if not driver.available:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Driver must be online to accept a ride.",
        )

    existing_active = await ride_repo.get_driver_active_ride(driver.id)
    if existing_active is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Finish the current active ride before accepting another one.",
        )

    ride = await ride_repo.find_by_id(ride_id)
    if ride is None:
        raise HTTPException(status_code=404, detail=f"Ride '{ride_id}' not found.")
    if ride.status != RideStatus.requested or ride.driver_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This ride is no longer available.",
        )

    updated = await ride_repo.update_status(
        ride_id,
        status=RideStatus.matched,
        driver_id=driver.id,
    )
    await driver_repo.update_availability(driver.id, available=False)

    if updated is None:
        raise HTTPException(status_code=404, detail="Ride not found after acceptance.")
    refreshed = await ride_repo.find_by_id(updated.id)
    return _serialize_driver_ride(refreshed)


@router.post("/rides/{ride_id}/reject", summary="Reject an incoming ride request")
async def reject_ride(
    ride_id: int,
    current_user: dict = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await _load_driver_profile(db, int(current_user["sub"]))
    ride = await RideRepository(db).find_by_id(ride_id)
    if ride is None:
        raise HTTPException(status_code=404, detail=f"Ride '{ride_id}' not found.")

    if ride.status != RideStatus.requested or ride.driver_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only unassigned incoming requests can be rejected.",
        )

    return {"ride_id": ride_id, "status": "rejected"}


@router.post("/rides/{ride_id}/status", summary="Advance the active ride lifecycle")
async def update_driver_ride_status(
    ride_id: int,
    body: DriverRideStatusRequest,
    current_user: dict = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
) -> dict:
    driver = await _load_driver_profile(db, int(current_user["sub"]))
    ride_repo = RideRepository(db)
    driver_repo = DriverRepository(db)
    payment_repo = PaymentRepository(db)

    ride = await ride_repo.find_by_id(ride_id)
    if ride is None:
        raise HTTPException(status_code=404, detail=f"Ride '{ride_id}' not found.")
    if ride.driver_id != driver.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This ride is not assigned to the current driver.",
        )

    target_status = _parse_status(body.status)
    allowed_statuses = _STATUS_FLOW.get(ride.status, set())
    if target_status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Invalid transition from '{ride.status.value}' to '{target_status.value}'."
            ),
        )

    updated = await ride_repo.update_status(ride_id, status=target_status, driver_id=driver.id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Ride not found after status update.")

    if target_status == RideStatus.completed:
        if updated.fare_amount is None:
            distance_km = updated.distance_km or 3.0
            price = _pricing_service.calculate_price(distance_km, 0.1)
            updated.fare_amount = price.total

        if updated.payment is None:
            await payment_repo.create(
                ride_id=updated.id,
                amount=float(updated.fare_amount or 0.0),
                status=PaymentStatus.paid,
            )

        await driver_repo.increment_total_trips(driver.id)
        await driver_repo.update_availability(driver.id, available=True)
        await db.flush()

    refreshed = await ride_repo.find_by_id(updated.id)
    if refreshed is None:
        raise HTTPException(status_code=404, detail="Ride not found after refresh.")
    return _serialize_driver_ride(refreshed)


async def _load_driver_profile(db: AsyncSession, user_id: int):
    driver = await DriverRepository(db).find_by_user_id(user_id)
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver profile not found for this account.",
        )
    return driver


def _serialize_driver_profile(driver, rides: list, active_ride) -> dict:
    today = datetime.now(tz=PKT).date()
    completed_today = [
        ride
        for ride in rides
        if ride.status == RideStatus.completed
        and _ride_time(ride).astimezone(PKT).date() == today
    ]
    earnings_today = round(sum(_ride_amount(ride) for ride in completed_today), 2)

    return {
        "id": driver.id,
        "user_id": driver.user_id,
        "name": driver.user.full_name if driver.user else f"Driver #{driver.id}",
        "email": driver.user.email if driver.user else None,
        "phone": driver.user.phone if driver.user else None,
        "rating": driver.rating,
        "available": driver.available,
        "vehicle_type": driver.vehicle_type,
        "total_trips": driver.total_trips,
        "is_active": driver.is_active,
        "lat": driver.lat,
        "lng": driver.lng,
        "rides_today": len(completed_today),
        "earnings_today": earnings_today,
        "active_ride_id": active_ride.id if active_ride else None,
    }


def _serialize_request(ride, driver_lat: float | None, driver_lng: float | None) -> dict:
    distance_from_driver = None
    if driver_lat is not None and driver_lng is not None:
        distance_from_driver = round(
            _haversine_km(driver_lat, driver_lng, ride.pickup_lat, ride.pickup_lng),
            2,
        )

    return {
        "id": ride.id,
        "status": ride.status.value if hasattr(ride.status, "value") else str(ride.status),
        "rider_name": ride.rider.full_name if ride.rider else f"Rider #{ride.rider_id}",
        "pickup_address": ride.pickup_address,
        "dropoff_address": ride.dropoff_address,
        "pickup_lat": ride.pickup_lat,
        "pickup_lng": ride.pickup_lng,
        "dropoff_lat": ride.dropoff_lat,
        "dropoff_lng": ride.dropoff_lng,
        "requested_at": ride.requested_at.isoformat() if ride.requested_at else None,
        "fare_amount": _ride_amount(ride),
        "distance_km": ride.distance_km,
        "distance_from_driver_km": distance_from_driver,
    }


def _serialize_driver_ride(ride) -> dict:
    if ride is None:
        return {}

    return {
        "id": ride.id,
        "status": ride.status.value if hasattr(ride.status, "value") else str(ride.status),
        "rider_name": ride.rider.full_name if ride.rider else f"Rider #{ride.rider_id}",
        "driver_name": (
            ride.driver.user.full_name
            if ride.driver is not None and ride.driver.user is not None
            else None
        ),
        "pickup_address": ride.pickup_address,
        "dropoff_address": ride.dropoff_address,
        "pickup_lat": ride.pickup_lat,
        "pickup_lng": ride.pickup_lng,
        "dropoff_lat": ride.dropoff_lat,
        "dropoff_lng": ride.dropoff_lng,
        "requested_at": ride.requested_at.isoformat() if ride.requested_at else None,
        "matched_at": ride.matched_at.isoformat() if ride.matched_at else None,
        "completed_at": ride.completed_at.isoformat() if ride.completed_at else None,
        "fare_amount": _ride_amount(ride),
        "surge_multiplier": ride.surge_multiplier,
        "distance_km": ride.distance_km,
    }


def _parse_status(raw_status: str) -> RideStatus:
    normalized = raw_status.strip().lower()
    mapping = {
        "en_route": RideStatus.en_route,
        "arrived": RideStatus.arrived,
        "in_progress": RideStatus.in_progress,
        "completed": RideStatus.completed,
    }
    parsed = mapping.get(normalized)
    if parsed is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported driver ride status.",
        )
    return parsed


def _ride_time(ride) -> datetime:
    if ride.payment is not None and ride.payment.created_at is not None:
        return ride.payment.created_at
    return ride.completed_at or ride.requested_at


def _ride_amount(ride) -> float:
    if ride.payment is not None and ride.payment.amount is not None:
        return round(float(ride.payment.amount), 2)
    return round(float(ride.fare_amount or 0.0), 2)


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)

    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lng / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
