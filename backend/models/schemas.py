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
    demand_level: float = Field(..., ge=0.0, le=1.0, description="Demand level between 0 and 1")


class PriceResult(BaseModel):
    base_fare: float
    surge_multiplier: float
    total: float
    breakdown: dict
