import math
import numpy as np
from datetime import datetime
from typing import List, Tuple

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from backend.models.schemas import Driver, MatchResult
from backend.services.drivers import DriversService


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return great-circle distance in kilometres between two lat/lng points."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class RideMatchingService:
    """
    ML-powered driver matching using a RandomForestClassifier trained on
    synthetic ride data.

    Features used per driver:
        - distance_km        : haversine distance from rider
        - driver_rating      : star rating (1–5)
        - availability_score : 1.0 if available else 0.0
        - time_of_day        : fractional hour (0–24) — captures demand patterns
    """

    N_SYNTHETIC = 2000
    RANDOM_STATE = 42

    def __init__(self, drivers_service: DriversService) -> None:
        self._drivers_service = drivers_service
        self._model = RandomForestClassifier(
            n_estimators=100,
            max_depth=6,
            random_state=self.RANDOM_STATE,
        )
        self._scaler = StandardScaler()
        self._trained = False
        self._train()

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def _train(self) -> None:
        """Build and fit the model on synthetic ride data."""
        rng = np.random.default_rng(self.RANDOM_STATE)

        distance_km = rng.uniform(0.1, 10.0, self.N_SYNTHETIC)
        driver_rating = rng.uniform(3.5, 5.0, self.N_SYNTHETIC)
        availability_score = rng.choice([0.0, 1.0], self.N_SYNTHETIC, p=[0.3, 0.7])
        time_of_day = rng.uniform(0.0, 24.0, self.N_SYNTHETIC)

        # Label: a driver is "good match" when close, highly rated, and available
        score = (
            (1.0 / (distance_km + 0.5)) * 3.0
            + (driver_rating - 3.5) * 2.0
            + availability_score * 2.5
            + np.sin(time_of_day / 24.0 * 2 * math.pi) * 0.5   # mild time-of-day effect
        )
        noise = rng.normal(0, 0.5, self.N_SYNTHETIC)
        labels = (score + noise > score.mean()).astype(int)

        X = np.column_stack([distance_km, driver_rating, availability_score, time_of_day])
        X_scaled = self._scaler.fit_transform(X)
        self._model.fit(X_scaled, labels)
        self._trained = True

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _build_feature_row(
        self,
        driver: Driver,
        rider_lat: float,
        rider_lng: float,
        time_of_day: float,
    ) -> np.ndarray:
        distance_km = _haversine_km(rider_lat, rider_lng, driver.lat, driver.lng)
        availability_score = 1.0 if driver.available else 0.0
        return np.array([[distance_km, driver.rating, availability_score, time_of_day]])

    def score_drivers(
        self,
        rider_lat: float,
        rider_lng: float,
        drivers: List[Driver],
    ) -> List[Tuple[Driver, float, float]]:
        """
        Score every driver and return a list of (driver, confidence, distance_km)
        sorted by confidence descending.
        """
        if not drivers:
            return []

        time_of_day = datetime.now().hour + datetime.now().minute / 60.0

        rows = []
        distances = []
        for driver in drivers:
            dist = _haversine_km(rider_lat, rider_lng, driver.lat, driver.lng)
            distances.append(dist)
            rows.append([dist, driver.rating, 1.0 if driver.available else 0.0, time_of_day])

        X = np.array(rows)
        X_scaled = self._scaler.transform(X)
        proba = self._model.predict_proba(X_scaled)[:, 1]  # probability of class 1 (good match)

        results = [
            (driver, float(conf), float(dist))
            for driver, conf, dist in zip(drivers, proba, distances)
        ]
        results.sort(key=lambda t: t[1], reverse=True)
        return results

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_best_match(self, rider_lat: float, rider_lng: float) -> MatchResult:
        """
        Return the best available driver for the given rider location.

        Raises:
            ValueError: if no available drivers exist.
        """
        available = self._drivers_service.get_available_drivers()
        if not available:
            raise ValueError("No available drivers at this time.")

        scored = self.score_drivers(rider_lat, rider_lng, available)
        best_driver, confidence, distance_km = scored[0]

        # ETA: assume average speed of 20 km/h in Karachi traffic
        eta_minutes = max(1, round((distance_km / 20.0) * 60))

        explanation = (
            f"Driver selected: {distance_km:.1f} km away, "
            f"{best_driver.rating:.1f}\u2605 rating, "
            f"{confidence * 100:.0f}% match confidence. "
            f"Vehicle: {best_driver.vehicle_type.capitalize()}. "
            f"ETA: ~{eta_minutes} min."
        )

        return MatchResult(
            driver=best_driver,
            confidence=round(confidence, 4),
            eta_minutes=eta_minutes,
            explanation=explanation,
        )
