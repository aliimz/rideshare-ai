"""
Location service — in-memory driver position store with optional movement simulation.

Coordinates are stored as plain dicts; all mutations return new dicts so that
callers always receive an independent snapshot (immutable-style updates).
"""

import logging
import random
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# Tiny jitter applied per simulation tick (degrees ≈ ±55 m at Lahore latitude)
_JITTER = 0.0005


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _jitter() -> float:
    """Return a small random offset in the range [-_JITTER, +_JITTER]."""
    return random.uniform(-_JITTER, _JITTER)


class LocationService:
    """
    In-memory store of driver locations.

    Data shape per driver:
        {
            "driver_id": str,
            "lat":        float,
            "lng":        float,
            "updated_at": str  # ISO-8601 UTC
        }
    """

    def __init__(self) -> None:
        # {driver_id: location_dict}  — mutable internal store; we expose copies
        self._locations: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def update_location(self, driver_id: str, lat: float, lng: float) -> dict[str, Any]:
        """
        Store or replace the position for *driver_id*.

        Returns the newly stored location dict (a fresh copy).
        """
        if not isinstance(driver_id, str) or not driver_id.strip():
            raise ValueError("driver_id must be a non-empty string")
        if not (-90 <= lat <= 90):
            raise ValueError(f"lat {lat} is out of range [-90, 90]")
        if not (-180 <= lng <= 180):
            raise ValueError(f"lng {lng} is out of range [-180, 180]")

        entry: dict[str, Any] = {
            "driver_id": driver_id,
            "lat": lat,
            "lng": lng,
            "updated_at": _now_iso(),
        }
        # Replace in store (new dict, no mutation of callers' references)
        self._locations = {**self._locations, driver_id: entry}
        logger.debug("Location updated: driver=%s lat=%.6f lng=%.6f", driver_id, lat, lng)
        return dict(entry)

    def get_all_locations(self) -> list[dict[str, Any]]:
        """Return a snapshot list of all stored driver locations."""
        return [dict(v) for v in self._locations.values()]

    def get_location(self, driver_id: str) -> dict[str, Any] | None:
        """Return the location for a specific driver, or *None* if unknown."""
        entry = self._locations.get(driver_id)
        return dict(entry) if entry else None

    def simulate_movement(self) -> list[dict[str, Any]]:
        """
        Slightly displace every tracked driver to create live-feeling movement.

        Returns the updated snapshot list.
        """
        updated: dict[str, dict[str, Any]] = {}
        for driver_id, entry in self._locations.items():
            updated[driver_id] = {
                **entry,
                "lat": entry["lat"] + _jitter(),
                "lng": entry["lng"] + _jitter(),
                "updated_at": _now_iso(),
            }

        self._locations = updated
        return self.get_all_locations()
