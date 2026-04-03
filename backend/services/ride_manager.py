"""
RideManager — in-memory ride lifecycle management.

Manages ride creation, driver matching, status transitions, and retrieval.
All state is stored in a plain dict (suitable for demo; swap for a DB in production).
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# Valid status transitions
# ---------------------------------------------------------------------------

_TRANSITIONS: dict[str, str] = {
    "matched":     "en_route",
    "en_route":    "arrived",
    "arrived":     "in_progress",
    "in_progress": "completed",
}

_ALL_STATUSES = {"requested", "matched", "en_route", "arrived", "in_progress", "completed"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_ride(
    ride_id: str,
    rider_id: str,
    pickup_lat: float,
    pickup_lng: float,
) -> dict:
    """Return a fresh Ride dict in the 'requested' state."""
    return {
        "id":           ride_id,
        "rider_id":     rider_id,
        "driver_id":    None,
        "status":       "requested",
        "pickup_lat":   pickup_lat,
        "pickup_lng":   pickup_lng,
        "fare":         None,
        "surge":        None,
        "requested_at": _now_iso(),
        "matched_at":   None,
        "completed_at": None,
    }


# ---------------------------------------------------------------------------
# RideManager
# ---------------------------------------------------------------------------

class RideManager:
    """
    In-memory ride store with lifecycle management.

    Ride dict schema
    ----------------
    id           : str       — UUID
    rider_id     : str
    driver_id    : str | None
    status       : str       — one of _ALL_STATUSES
    pickup_lat   : float
    pickup_lng   : float
    fare         : float | None
    surge        : float | None
    requested_at : str       — ISO-8601 UTC
    matched_at   : str | None
    completed_at : str | None
    """

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_ride(
        self,
        rider_id: str,
        pickup_lat: float,
        pickup_lng: float,
    ) -> dict:
        """
        Create a new ride in the 'requested' state.

        Args:
            rider_id:   Identifier for the rider.
            pickup_lat: Pickup latitude.
            pickup_lng: Pickup longitude.

        Returns:
            New Ride dict.

        Raises:
            ValueError: If coordinates are out of range.
        """
        if not (-90 <= pickup_lat <= 90):
            raise ValueError("pickup_lat must be between -90 and 90.")
        if not (-180 <= pickup_lng <= 180):
            raise ValueError("pickup_lng must be between -180 and 180.")
        if not rider_id or not isinstance(rider_id, str):
            raise ValueError("rider_id must be a non-empty string.")

        ride_id = str(uuid.uuid4())
        ride = _build_ride(ride_id, rider_id, pickup_lat, pickup_lng)
        self._store[ride_id] = ride
        return dict(ride)

    def match_driver(self, ride_id: str, driver_id: str) -> dict:
        """
        Assign a driver to a ride and transition its status to 'matched'.

        Args:
            ride_id:   ID of the ride to update.
            driver_id: ID of the driver being assigned.

        Returns:
            Updated Ride dict (immutable copy).

        Raises:
            KeyError:   If ride_id is not found.
            ValueError: If the ride is not in 'requested' state.
        """
        ride = self._get_mutable(ride_id)

        if ride["status"] != "requested":
            raise ValueError(
                f"Cannot match driver: ride is in '{ride['status']}' state, expected 'requested'."
            )
        if not driver_id or not isinstance(driver_id, str):
            raise ValueError("driver_id must be a non-empty string.")

        updated = {
            **ride,
            "driver_id":  driver_id,
            "status":     "matched",
            "matched_at": _now_iso(),
        }
        self._store[ride_id] = updated
        return dict(updated)

    def update_status(self, ride_id: str, status: str) -> dict:
        """
        Advance the ride status along the permitted transition chain:
            matched -> en_route -> arrived -> in_progress -> completed

        Args:
            ride_id: ID of the ride.
            status:  Target status (must be the immediate next state).

        Returns:
            Updated Ride dict (immutable copy).

        Raises:
            KeyError:   If ride_id is not found.
            ValueError: If the transition is not permitted.
        """
        if status not in _ALL_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. Must be one of: {sorted(_ALL_STATUSES)}."
            )

        ride = self._get_mutable(ride_id)
        current = ride["status"]
        expected_next = _TRANSITIONS.get(current)

        if expected_next is None:
            raise ValueError(
                f"Ride '{ride_id}' is in terminal or pre-transition state '{current}' "
                "and cannot be advanced further."
            )
        if status != expected_next:
            raise ValueError(
                f"Invalid transition: '{current}' -> '{status}'. "
                f"Expected next status: '{expected_next}'."
            )

        timestamp_field = "completed_at" if status == "completed" else None

        updated = {
            **ride,
            "status": status,
            **({"completed_at": _now_iso()} if timestamp_field else {}),
        }
        self._store[ride_id] = updated
        return dict(updated)

    def get_ride(self, ride_id: str) -> dict:
        """
        Return a Ride dict by ID.

        Raises:
            KeyError: If ride_id is not found.
        """
        ride = self._store.get(ride_id)
        if ride is None:
            raise KeyError(f"Ride '{ride_id}' not found.")
        return dict(ride)

    def get_active_rides(self) -> list[dict]:
        """
        Return all rides that are not in 'completed' state, sorted by
        requested_at descending (newest first).
        """
        active = [
            dict(ride)
            for ride in self._store.values()
            if ride["status"] != "completed"
        ]
        active.sort(key=lambda r: r["requested_at"], reverse=True)
        return active

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_mutable(self, ride_id: str) -> dict:
        """Return the stored ride dict or raise KeyError."""
        ride = self._store.get(ride_id)
        if ride is None:
            raise KeyError(f"Ride '{ride_id}' not found.")
        return ride
