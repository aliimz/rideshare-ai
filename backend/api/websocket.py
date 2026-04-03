"""
WebSocket module — real-time driver location tracking.

Endpoint:   ws://localhost:8000/ws/{client_id}

Message protocol (JSON):
  Client → Server (driver location update):
      {
          "type":      "location_update",
          "driver_id": "<str>",
          "lat":       <float>,
          "lng":       <float>
      }

  Server → Client (on connect — current positions):
      {
          "type":    "initial_positions",
          "drivers": [ { "driver_id", "lat", "lng", "updated_at" }, … ]
      }

  Server → All clients (broadcast after a driver moves):
      {
          "type":   "driver_moved",
          "driver": { "driver_id", "lat", "lng", "updated_at" }
      }

  Server → Client (error):
      {
          "type":    "error",
          "message": "<str>"
      }
"""

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.location import LocationService

logger = logging.getLogger(__name__)

ws_router = APIRouter()

# ---------------------------------------------------------------------------
# Module-level singletons shared across all WebSocket connections
# ---------------------------------------------------------------------------
location_service = LocationService()

# Seed with Lahore drivers so WebSocket sends real positions immediately
_LAHORE_DRIVERS = [
    (1,  31.5204, 74.3587), (2,  31.5232, 74.3621), (3,  31.5180, 74.3553),
    (4,  31.5251, 74.3648), (5,  31.5195, 74.3609), (6,  31.5219, 74.3541),
    (7,  31.5170, 74.3634), (8,  31.5243, 74.3596), (9,  31.5188, 74.3671),
    (10, 31.5260, 74.3574), (11, 31.5174, 74.3618), (12, 31.5228, 74.3657),
    (13, 31.5202, 74.3549), (14, 31.5215, 74.3636), (15, 31.5156, 74.3601),
    (16, 31.5237, 74.3526), (17, 31.5183, 74.3686), (18, 31.5248, 74.3613),
    (19, 31.5165, 74.3556), (20, 31.5222, 74.3631),
]
for _id, _lat, _lng in _LAHORE_DRIVERS:
    location_service.update_location(str(_id), _lat, _lng)


# ---------------------------------------------------------------------------
# Connection manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    """Maintains a registry of active WebSocket connections."""

    def __init__(self) -> None:
        # {client_id: WebSocket}
        self._active: dict[str, WebSocket] = {}

    # ---- connection lifecycle --------------------------------------------

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept the connection and register it under *client_id*."""
        await websocket.accept()
        self._active = {**self._active, client_id: websocket}
        logger.info("WebSocket connected: client_id=%s  total=%d", client_id, len(self._active))

    def disconnect(self, client_id: str) -> None:
        """Remove *client_id* from the registry (idempotent)."""
        self._active = {k: v for k, v in self._active.items() if k != client_id}
        logger.info("WebSocket disconnected: client_id=%s  total=%d", client_id, len(self._active))

    # ---- sending ---------------------------------------------------------

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send *message* to every connected client; silently drop broken sockets."""
        payload = json.dumps(message)
        dead: list[str] = []
        for client_id, ws in self._active.items():
            try:
                await ws.send_text(payload)
            except Exception:
                logger.warning("Broadcast failed for client_id=%s — marking for removal", client_id)
                dead.append(client_id)

        # Clean up sockets that errored during broadcast
        if dead:
            self._active = {k: v for k, v in self._active.items() if k not in dead}

    async def send_to(self, client_id: str, message: dict[str, Any]) -> None:
        """Send *message* to a single client identified by *client_id*."""
        ws = self._active.get(client_id)
        if ws is None:
            logger.debug("send_to: client_id=%s not found (already disconnected?)", client_id)
            return
        try:
            await ws.send_text(json.dumps(message))
        except Exception as exc:
            logger.warning("send_to failed for client_id=%s: %s", client_id, exc)
            self.disconnect(client_id)


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@ws_router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
    """
    Accept a WebSocket connection, send the current driver snapshot, then
    relay location updates from drivers to all connected clients.
    """
    await manager.connect(websocket, client_id)

    # Send current positions immediately on connect
    current_positions = location_service.get_all_locations()
    await manager.send_to(
        client_id,
        {"type": "initial_positions", "drivers": current_positions},
    )

    # Start simulation loop — broadcast movement every 3 seconds
    async def _simulation_loop() -> None:
        while True:
            await asyncio.sleep(3)
            updated = location_service.simulate_movement()
            await manager.broadcast({"type": "drivers_update", "drivers": updated})

    sim_task = asyncio.create_task(_simulation_loop())

    try:
        while True:
            raw = await websocket.receive_text()

            # Parse — reject non-JSON gracefully
            try:
                data: dict[str, Any] = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_to(
                    client_id,
                    {"type": "error", "message": "Invalid JSON payload."},
                )
                continue

            msg_type = data.get("type")

            if msg_type == "location_update":
                _handle_location_update(data, client_id)
                await manager.broadcast(_build_driver_moved(data))

            else:
                await manager.send_to(
                    client_id,
                    {"type": "error", "message": f"Unknown message type: {msg_type!r}"},
                )

    except WebSocketDisconnect:
        sim_task.cancel()
        manager.disconnect(client_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _handle_location_update(data: dict[str, Any], sender_client_id: str) -> None:
    """Validate and persist a location_update message from a driver client."""
    driver_id = data.get("driver_id")
    lat = data.get("lat")
    lng = data.get("lng")

    if not isinstance(driver_id, str) or not driver_id.strip():
        logger.warning("location_update from %s missing valid driver_id", sender_client_id)
        return
    if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
        logger.warning(
            "location_update from %s has non-numeric lat/lng: lat=%r lng=%r",
            sender_client_id, lat, lng,
        )
        return

    try:
        location_service.update_location(driver_id, float(lat), float(lng))
    except ValueError as exc:
        logger.warning("location_update rejected: %s", exc)


def _build_driver_moved(data: dict[str, Any]) -> dict[str, Any]:
    """Build the broadcast payload after a driver location update."""
    driver_id = data.get("driver_id", "")
    entry = location_service.get_location(driver_id)
    return {
        "type": "driver_moved",
        "driver": entry or {"driver_id": driver_id, "lat": data.get("lat"), "lng": data.get("lng")},
    }
