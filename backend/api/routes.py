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


@router.get("/heatmap", summary="Get demand heatmap points for Karachi")
def get_heatmap() -> List[dict]:
    """
    Return demand hotspot points across Karachi for visualisation.
    Each point has lat, lng, and intensity (0.0–1.0).
    """
    hotspots = [
        # Central Business District / Saddar
        {"lat": 24.8607, "lng": 67.0011, "intensity": 0.95},
        {"lat": 24.8580, "lng": 67.0040, "intensity": 0.88},
        # Clifton / Defence
        {"lat": 24.8138, "lng": 67.0300, "intensity": 0.90},
        {"lat": 24.8200, "lng": 67.0450, "intensity": 0.85},
        {"lat": 24.8050, "lng": 67.0380, "intensity": 0.78},
        # North Nazimabad
        {"lat": 24.9200, "lng": 67.0350, "intensity": 0.72},
        {"lat": 24.9350, "lng": 67.0420, "intensity": 0.65},
        # Gulshan-e-Iqbal
        {"lat": 24.9200, "lng": 67.0950, "intensity": 0.80},
        {"lat": 24.9100, "lng": 67.1100, "intensity": 0.74},
        # Korangi Industrial Area
        {"lat": 24.8200, "lng": 67.1300, "intensity": 0.60},
        {"lat": 24.8050, "lng": 67.1450, "intensity": 0.55},
        # Karachi Airport / PAF Base
        {"lat": 24.9008, "lng": 67.1681, "intensity": 0.82},
        # Malir
        {"lat": 24.8800, "lng": 67.2000, "intensity": 0.50},
        # Orangi Town
        {"lat": 24.9500, "lng": 66.9800, "intensity": 0.67},
        {"lat": 24.9600, "lng": 66.9700, "intensity": 0.58},
        # Lyari
        {"lat": 24.8550, "lng": 66.9850, "intensity": 0.70},
        # Landhi
        {"lat": 24.8450, "lng": 67.2200, "intensity": 0.45},
        # F.B. Area / Gulberg
        {"lat": 24.9000, "lng": 67.0650, "intensity": 0.75},
        # Shahrah-e-Faisal corridor
        {"lat": 24.8750, "lng": 67.0650, "intensity": 0.88},
        {"lat": 24.8650, "lng": 67.0500, "intensity": 0.83},
        # Karachi Port / Kemari
        {"lat": 24.8400, "lng": 66.9800, "intensity": 0.62},
        # Gulistan-e-Jauhar
        {"lat": 24.9050, "lng": 67.1350, "intensity": 0.76},
        # University Road
        {"lat": 24.9300, "lng": 67.1000, "intensity": 0.70},
        # DHA Phase 8 / Khayaban
        {"lat": 24.7900, "lng": 67.0700, "intensity": 0.84},
        # Scheme 33
        {"lat": 24.9700, "lng": 67.1300, "intensity": 0.48},
    ]
    return hotspots
