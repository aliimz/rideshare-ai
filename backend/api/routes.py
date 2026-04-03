from typing import List

from fastapi import APIRouter, HTTPException

from backend.models.schemas import (
    Driver,
    MatchResult,
    PriceRequest,
    PriceResult,
    RideRequest,
)
from backend.services.drivers import DriversService
from backend.services.matching import RideMatchingService
from backend.services.pricing import DynamicPricingService

router = APIRouter(prefix="/api")

# ---------------------------------------------------------------------------
# Service singletons — initialised once at import time so the RF model is
# trained only once when the server starts.
# ---------------------------------------------------------------------------
_drivers_service = DriversService()
_matching_service = RideMatchingService(drivers_service=_drivers_service)
_pricing_service = DynamicPricingService()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/match", response_model=MatchResult, summary="Match rider to best driver")
def match_driver(request: RideRequest) -> MatchResult:
    """
    Accept a rider's GPS coordinates and return the best matched driver
    with an AI confidence score and human-readable explanation.
    """
    if not (-90 <= request.rider_lat <= 90):
        raise HTTPException(status_code=422, detail="rider_lat must be between -90 and 90.")
    if not (-180 <= request.rider_lng <= 180):
        raise HTTPException(status_code=422, detail="rider_lng must be between -180 and 180.")

    try:
        result = _matching_service.get_best_match(request.rider_lat, request.rider_lng)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return result


@router.get("/drivers", response_model=List[Driver], summary="List all drivers")
def list_drivers() -> List[Driver]:
    """Return all 20 drivers with their current location, status, rating, and vehicle type."""
    return _drivers_service.get_all_drivers()


@router.post("/price", response_model=PriceResult, summary="Calculate dynamic price")
def calculate_price(request: PriceRequest) -> PriceResult:
    """
    Accept distance and demand level, return base fare, surge multiplier,
    total fare, and a full PKR breakdown.
    """
    return _pricing_service.calculate_price(request.distance_km, request.demand_level)


@router.get("/heatmap", summary="Get demand heatmap points for Lahore")
def get_heatmap() -> List[dict]:
    """
    Return demand hotspot points across Lahore for visualisation.
    Each point has lat, lng, and intensity (0.0–1.0).
    """
    hotspots = [
        # Mall Road / City Centre
        {"lat": 31.5204, "lng": 74.3587, "intensity": 0.95},
        {"lat": 31.5180, "lng": 74.3620, "intensity": 0.88},
        # Gulberg
        {"lat": 31.5120, "lng": 74.3290, "intensity": 0.90},
        {"lat": 31.5090, "lng": 74.3350, "intensity": 0.85},
        # DHA Lahore
        {"lat": 31.4697, "lng": 74.3936, "intensity": 0.82},
        {"lat": 31.4750, "lng": 74.4000, "intensity": 0.78},
        # Johar Town
        {"lat": 31.4700, "lng": 74.2800, "intensity": 0.80},
        {"lat": 31.4650, "lng": 74.2750, "intensity": 0.74},
        # Bahria Town
        {"lat": 31.3656, "lng": 74.1780, "intensity": 0.70},
        {"lat": 31.3700, "lng": 74.1850, "intensity": 0.65},
        # Lahore Airport (Allama Iqbal)
        {"lat": 31.5216, "lng": 74.4036, "intensity": 0.88},
        # Model Town
        {"lat": 31.4840, "lng": 74.3180, "intensity": 0.76},
        # Wapda Town
        {"lat": 31.4550, "lng": 74.2650, "intensity": 0.68},
        # Cavalry Ground
        {"lat": 31.5350, "lng": 74.3800, "intensity": 0.72},
        # Cantt / Shadman
        {"lat": 31.5430, "lng": 74.3290, "intensity": 0.84},
        {"lat": 31.5380, "lng": 74.3200, "intensity": 0.79},
        # Garden Town
        {"lat": 31.5060, "lng": 74.3220, "intensity": 0.75},
        # Township
        {"lat": 31.4770, "lng": 74.2590, "intensity": 0.60},
        # Iqbal Town
        {"lat": 31.4930, "lng": 74.2980, "intensity": 0.71},
        # Faisal Town
        {"lat": 31.4860, "lng": 74.2870, "intensity": 0.66},
        # Raiwind Road corridor
        {"lat": 31.4400, "lng": 74.3100, "intensity": 0.55},
        # Thokar Niaz Baig
        {"lat": 31.4230, "lng": 74.2760, "intensity": 0.50},
        # GT Road / Shahdara
        {"lat": 31.5900, "lng": 74.3450, "intensity": 0.62},
        # Allama Iqbal Town
        {"lat": 31.4980, "lng": 74.3060, "intensity": 0.73},
        # Liberty Market
        {"lat": 31.5140, "lng": 74.3380, "intensity": 0.91},
    ]
    return hotspots
