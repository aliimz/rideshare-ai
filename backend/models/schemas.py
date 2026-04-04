from pydantic import BaseModel, Field
from typing import Optional


class RideRequest(BaseModel):
    rider_lat: float = Field(..., description="Rider latitude")
    rider_lng: float = Field(..., description="Rider longitude")


class Driver(BaseModel):
    id: int
    name: str
    lat: float
    lng: float
    rating: float
    available: bool
    vehicle_type: str


class MatchResult(BaseModel):
    driver: Driver
    confidence: float
    eta_minutes: int
    explanation: str


class PriceRequest(BaseModel):
    distance_km: float = Field(..., gt=0, description="Distance in kilometers")
    demand_level: float | None = Field(
        None, ge=0.0, le=1.0, description="Optional demand level; predicted via ML if omitted"
    )
    pickup_lat: float | None = Field(None, ge=-90, le=90, description="Pickup latitude for demand prediction")
    pickup_lng: float | None = Field(None, ge=-180, le=180, description="Pickup longitude for demand prediction")


class PriceResult(BaseModel):
    base_fare: float
    surge_multiplier: float
    total: float
    breakdown: dict
