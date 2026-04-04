"""
Async helpers for logging AI match decisions and their outcomes.

These functions bridge the synchronous matching service with the async DB layer.
"""

import math
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import AsyncSessionLocal
from backend.db.models import MatchOutcome, Ride, RideStatus
from backend.models.schemas import Driver, MatchResult


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


async def log_match_decision(
    ride_id: int | None,
    driver: Driver,
    rider_lat: float,
    rider_lng: float,
) -> MatchOutcome:
    """Persist the features used at match time so we can retrain later."""
    distance_km = _haversine_km(rider_lat, rider_lng, driver.lat, driver.lng)
    now = datetime.now()
    time_of_day = now.hour + now.minute / 60.0

    outcome = MatchOutcome(
        ride_id=ride_id,
        driver_id=driver.id,
        rider_lat=rider_lat,
        rider_lng=rider_lng,
        distance_km=distance_km,
        driver_rating=driver.rating,
        availability_score=1.0 if driver.available else 0.0,
        time_of_day=time_of_day,
        day_of_week=now.weekday(),
        driver_acceptance_rate=0.85,
    )

    async with AsyncSessionLocal() as session:
        session.add(outcome)
        await session.commit()
        await session.refresh(outcome)
        return outcome


async def update_match_outcome(
    ride_id: int,
    actual_rating: float | None = None,
    cancelled: bool | None = None,
    actual_wait_minutes: float | None = None,
) -> None:
    """
    Update the MatchOutcome for a ride once it finishes.

    outcome_label heuristic:
        - cancelled          → 0
        - rating >= 4.5 and wait <= 10 min → 1
        - otherwise          → 0
    """
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(MatchOutcome).where(MatchOutcome.ride_id == ride_id)
        )
        match_outcome = result.scalar_one_or_none()
        if match_outcome is None:
            return

        match_outcome.actual_rating = actual_rating
        match_outcome.cancelled = cancelled
        match_outcome.actual_wait_minutes = actual_wait_minutes

        if cancelled:
            match_outcome.outcome_label = 0
        elif actual_rating is not None and actual_wait_minutes is not None:
            match_outcome.outcome_label = 1 if (actual_rating >= 4.5 and actual_wait_minutes <= 10) else 0
        elif actual_rating is not None:
            match_outcome.outcome_label = 1 if actual_rating >= 4.5 else 0
        elif actual_wait_minutes is not None:
            match_outcome.outcome_label = 1 if actual_wait_minutes <= 10 else 0
        else:
            match_outcome.outcome_label = None

        await session.commit()


async def load_match_outcomes_for_training(min_records: int = 10) -> list[dict]:
    """Load completed MatchOutcome rows that have a known label."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(MatchOutcome).where(MatchOutcome.outcome_label.isnot(None))
        )
        records = result.scalars().all()
        if len(records) < min_records:
            return []

        return [
            {
                "distance_km": r.distance_km,
                "driver_rating": r.driver_rating,
                "availability_score": r.availability_score,
                "time_of_day": r.time_of_day,
                "day_of_week": r.day_of_week,
                "driver_acceptance_rate": r.driver_acceptance_rate,
                "outcome_label": r.outcome_label,
            }
            for r in records
        ]
