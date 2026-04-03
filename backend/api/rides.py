"""
Ride management endpoints: create, retrieve, status update, and history.

Uses an in-memory store (dict keyed by ride_id) in place of a real database.
"""

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.core.dependencies import get_current_user, require_driver, require_rider

router = APIRouter(prefix="/rides", tags=["rides"])

# ---------------------------------------------------------------------------
# In-memory ride store  {ride_id: ride_record}
# ---------------------------------------------------------------------------
_rides: dict[str, dict] = {}

RideStatus = Literal["requested", "accepted", "in_progress", "completed", "cancelled"]


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class CreateRideRequest(BaseModel):
    pickup_lat: float = Field(..., ge=-90, le=90, description="Pickup latitude")
    pickup_lng: float = Field(..., ge=-180, le=180, description="Pickup longitude")
    dropoff_lat: float = Field(..., ge=-90, le=90, description="Dropoff latitude")
    dropoff_lng: float = Field(..., ge=-180, le=180, description="Dropoff longitude")
    pickup_address: str = Field(..., min_length=1)
    dropoff_address: str = Field(..., min_length=1)
    vehicle_type: Literal["economy", "comfort", "xl"] = "economy"


class UpdateStatusRequest(BaseModel):
    status: RideStatus


class RideResponse(BaseModel):
    id: str
    rider_id: str
    driver_id: str | None
    pickup_lat: float
    pickup_lng: float
    dropoff_lat: float
    dropoff_lng: float
    pickup_address: str
    dropoff_address: str
    vehicle_type: str
    status: str
    created_at: str
    updated_at: str


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _ride_to_response(ride: dict) -> RideResponse:
    return RideResponse(**ride)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=RideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request a new ride (rider only)",
)
def create_ride(
    body: CreateRideRequest,
    current_user: dict = Depends(require_rider),
) -> RideResponse:
    """
    Create a new ride request for the authenticated rider.

    The initial status is ``requested``.
    """
    now = _utcnow()
    ride_id = str(uuid.uuid4())
    ride: dict = {
        "id": ride_id,
        "rider_id": current_user["sub"],
        "driver_id": None,
        "pickup_lat": body.pickup_lat,
        "pickup_lng": body.pickup_lng,
        "dropoff_lat": body.dropoff_lat,
        "dropoff_lng": body.dropoff_lng,
        "pickup_address": body.pickup_address,
        "dropoff_address": body.dropoff_address,
        "vehicle_type": body.vehicle_type,
        "status": "requested",
        "created_at": now,
        "updated_at": now,
    }
    _rides[ride_id] = ride
    return _ride_to_response(ride)


@router.get(
    "/history",
    response_model=list[RideResponse],
    summary="Retrieve the authenticated rider's ride history",
)
def ride_history(
    current_user: dict = Depends(get_current_user),
) -> list[RideResponse]:
    """
    Return all rides belonging to the authenticated user.

    Both riders (filtered by ``rider_id``) and drivers (filtered by
    ``driver_id``) can call this endpoint.
    """
    user_id = current_user["sub"]
    role = current_user.get("role")

    if role == "driver":
        matching = [r for r in _rides.values() if r.get("driver_id") == user_id]
    else:
        matching = [r for r in _rides.values() if r["rider_id"] == user_id]

    return [_ride_to_response(r) for r in matching]


@router.get(
    "/{ride_id}",
    response_model=RideResponse,
    summary="Retrieve a single ride by ID",
)
def get_ride(
    ride_id: str,
    current_user: dict = Depends(get_current_user),
) -> RideResponse:
    """
    Return details for *ride_id*.

    Raises HTTP 404 if the ride does not exist.
    Raises HTTP 403 if the caller is neither the rider nor the assigned driver.
    """
    ride = _rides.get(ride_id)
    if ride is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ride '{ride_id}' not found.",
        )

    user_id = current_user["sub"]
    is_participant = (
        ride["rider_id"] == user_id or ride.get("driver_id") == user_id
    )
    if not is_participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this ride.",
        )

    return _ride_to_response(ride)


@router.patch(
    "/{ride_id}/status",
    response_model=RideResponse,
    summary="Update ride status (driver only)",
)
def update_ride_status(
    ride_id: str,
    body: UpdateStatusRequest,
    current_user: dict = Depends(require_driver),
) -> RideResponse:
    """
    Allow an authenticated driver to update the status of *ride_id*.

    - When a driver sets status to ``accepted``, their ``driver_id`` is
      recorded on the ride.
    - Raises HTTP 404 if the ride does not exist.
    - Raises HTTP 409 if a different driver has already accepted the ride.
    """
    ride = _rides.get(ride_id)
    if ride is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ride '{ride_id}' not found.",
        )

    driver_id = current_user["sub"]

    # Prevent a second driver from hijacking an already-accepted ride.
    if (
        ride.get("driver_id") is not None
        and ride["driver_id"] != driver_id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This ride has already been accepted by another driver.",
        )

    updated_ride = {
        **ride,
        "status": body.status,
        "updated_at": _utcnow(),
    }

    # Assign driver when they accept the ride.
    if body.status == "accepted":
        updated_ride = {**updated_ride, "driver_id": driver_id}

    _rides[ride_id] = updated_ride
    return _ride_to_response(updated_ride)
