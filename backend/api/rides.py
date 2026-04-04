"""
Ride management endpoints: create, retrieve, status update, and history.

Uses PostgreSQL via AsyncSession + RideRepository.
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.dependencies import get_current_user, require_driver, require_rider
from backend.db.database import get_db
from backend.db.models import Driver, RideStatus
from backend.db.repositories import RideRepository

router = APIRouter(prefix="/rides", tags=["rides"])

StatusLiteral = Literal["requested", "accepted", "in_progress", "completed", "cancelled"]

# Map incoming status strings to RideStatus enum values
_STATUS_MAP: dict[str, RideStatus] = {
    "requested": RideStatus.requested,
    "accepted": RideStatus.matched,      # "accepted" by driver = "matched" in DB
    "in_progress": RideStatus.in_progress,
    "completed": RideStatus.completed,
    "cancelled": RideStatus.cancelled,
}


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------


class CreateRideRequest(BaseModel):
    pickup_lat: float = Field(..., ge=-90, le=90)
    pickup_lng: float = Field(..., ge=-180, le=180)
    dropoff_lat: float = Field(..., ge=-90, le=90)
    dropoff_lng: float = Field(..., ge=-180, le=180)
    pickup_address: str = Field(..., min_length=1)
    dropoff_address: str = Field(..., min_length=1)
    vehicle_type: Literal["economy", "comfort", "xl"] = "economy"


class UpdateStatusRequest(BaseModel):
    status: StatusLiteral


class RideResponse(BaseModel):
    id: int
    rider_id: int
    driver_id: int | None
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
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=RideResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request a new ride (rider only)",
)
async def create_ride(
    body: CreateRideRequest,
    current_user: dict = Depends(require_rider),
    db: AsyncSession = Depends(get_db),
) -> RideResponse:
    """Create a new ride request. Initial status is ``requested``."""
    rider_id = int(current_user["sub"])
    repo = RideRepository(db)

    ride = await repo.create(
        rider_id=rider_id,
        pickup_lat=body.pickup_lat,
        pickup_lng=body.pickup_lng,
        dropoff_lat=body.dropoff_lat,
        dropoff_lng=body.dropoff_lng,
        pickup_address=body.pickup_address,
        dropoff_address=body.dropoff_address,
    )

    return _to_response(ride, body.pickup_address, body.dropoff_address, body.vehicle_type)


@router.get(
    "/history",
    response_model=list[RideResponse],
    summary="Retrieve the authenticated user's ride history",
)
async def ride_history(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RideResponse]:
    """Return all rides belonging to the authenticated user."""
    user_id = int(current_user["sub"])
    repo = RideRepository(db)
    rides = await repo.get_rider_history(user_id)
    return [_to_response(r) for r in rides]


@router.get(
    "/{ride_id}",
    response_model=RideResponse,
    summary="Retrieve a single ride by ID",
)
async def get_ride(
    ride_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RideResponse:
    """Return details for *ride_id*. Raises 404 if not found, 403 if not a participant."""
    repo = RideRepository(db)
    ride = await repo.find_by_id(ride_id)

    if ride is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ride '{ride_id}' not found.",
        )

    user_id = int(current_user["sub"])
    role = current_user.get("role")

    # Riders can only see their own rides; drivers can see rides assigned to them
    is_rider_owner = (ride.rider_id == user_id)
    is_assigned_driver = (ride.driver_id is not None and role == "driver")

    if not (is_rider_owner or is_assigned_driver):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this ride.",
        )

    return _to_response(ride)


@router.patch(
    "/{ride_id}/status",
    response_model=RideResponse,
    summary="Update ride status (driver only)",
)
async def update_ride_status(
    ride_id: int,
    body: UpdateStatusRequest,
    current_user: dict = Depends(require_driver),
    db: AsyncSession = Depends(get_db),
) -> RideResponse:
    """
    Allow an authenticated driver to update the status of *ride_id*.

    When status becomes ``accepted``, the driver's DB record is linked to the ride.
    """
    repo = RideRepository(db)
    ride = await repo.find_by_id(ride_id)

    if ride is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ride '{ride_id}' not found.",
        )

    user_id = int(current_user["sub"])
    new_status = _STATUS_MAP.get(body.status, RideStatus.requested)

    # Resolve user_id → driver_id for the assignment
    driver_db_id: int | None = None
    if body.status == "accepted":
        result = await db.execute(
            select(Driver).where(Driver.user_id == user_id)
        )
        driver_record = result.scalar_one_or_none()
        if driver_record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Driver profile not found for this user.",
            )

        # Prevent another driver hijacking an already-accepted ride
        if ride.driver_id is not None and ride.driver_id != driver_record.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This ride has already been accepted by another driver.",
            )

        driver_db_id = driver_record.id

    updated = await repo.update_status(ride_id, status=new_status, driver_id=driver_db_id)
    if updated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ride not found.")

    return _to_response(updated)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _to_response(
    ride,
    pickup_address: str = "",
    dropoff_address: str = "",
    vehicle_type: str = "economy",
) -> RideResponse:
    """Convert an ORM Ride instance to a RideResponse."""
    return RideResponse(
        id=ride.id,
        rider_id=ride.rider_id,
        driver_id=ride.driver_id,
        pickup_lat=ride.pickup_lat,
        pickup_lng=ride.pickup_lng,
        dropoff_lat=ride.dropoff_lat,
        dropoff_lng=ride.dropoff_lng,
        pickup_address=ride.pickup_address or pickup_address,
        dropoff_address=ride.dropoff_address or dropoff_address,
        vehicle_type=vehicle_type,
        status=ride.status.value if hasattr(ride.status, "value") else str(ride.status),
        created_at=ride.requested_at.isoformat() if ride.requested_at else "",
        updated_at=(
            ride.completed_at or ride.matched_at or ride.requested_at
        ).isoformat() if ride.requested_at else "",
    )
