"""
ML-powered driver matching with real-data retraining.

Trains a GradientBoostingClassifier on synthetic data initially,
then retrains on logged MatchOutcome records as real rides complete.
"""

import math
from datetime import datetime
from typing import List, Optional, Tuple

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
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
    Gradient-boosted driver matching.

    Features per driver:
        - distance_km           : haversine distance from rider
        - driver_rating         : star rating (1–5)
        - availability_score    : 1.0 if available else 0.0
        - time_of_day           : fractional hour (0–24)
        - day_of_week           : 0=Monday … 6=Sunday
        - driver_acceptance_rate: historical acceptance (0–1)
    """

    N_SYNTHETIC = 2000
    RANDOM_STATE = 42

    def __init__(self, drivers_service: DriversService) -> None:
        self._drivers_service = drivers_service
        self._model = GradientBoostingClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=self.RANDOM_STATE,
        )
        self._scaler = StandardScaler()
        self._trained = False
        self._train_synthetic()

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def _train_synthetic(self) -> None:
        """Initial training on synthetic data so the app works immediately."""
        X, y = self._build_synthetic_dataset(self.N_SYNTHETIC)
        X_scaled = self._scaler.fit_transform(X)
        self._model.fit(X_scaled, y)
        self._trained = True

    def _build_synthetic_dataset(self, n: int) -> Tuple[np.ndarray, np.ndarray]:
        rng = np.random.default_rng(self.RANDOM_STATE)

        distance_km = rng.uniform(0.1, 10.0, n)
        driver_rating = rng.uniform(3.5, 5.0, n)
        availability_score = rng.choice([0.0, 1.0], n, p=[0.3, 0.7])
        time_of_day = rng.uniform(0.0, 24.0, n)
        day_of_week = rng.integers(0, 7, n)
        driver_acceptance_rate = rng.beta(7, 2, n)  # skewed high

        score = (
            (1.0 / (distance_km + 0.5)) * 3.0
            + (driver_rating - 3.5) * 2.0
            + availability_score * 2.5
            + np.sin(time_of_day / 24.0 * 2 * math.pi) * 0.5
            + driver_acceptance_rate * 1.0
        )
        noise = rng.normal(0, 0.5, n)
        labels = (score + noise > score.mean()).astype(int)

        X = np.column_stack(
            [distance_km, driver_rating, availability_score, time_of_day, day_of_week, driver_acceptance_rate]
        )
        return X, labels

    def retrain_with_outcomes(self, outcomes: List[dict]) -> bool:
        """
        Retrain the model mixing synthetic data with real MatchOutcome records.

        outcomes: list of dicts with keys:
            distance_km, driver_rating, availability_score, time_of_day,
            day_of_week, driver_acceptance_rate, outcome_label (0 or 1)
        """
        if len(outcomes) < 10:
            return False

        X_syn, y_syn = self._build_synthetic_dataset(self.N_SYNTHETIC)

        real_X = []
        real_y = []
        for o in outcomes:
            real_X.append(
                [
                    o["distance_km"],
                    o["driver_rating"],
                    o["availability_score"],
                    o["time_of_day"],
                    o["day_of_week"],
                    o.get("driver_acceptance_rate", 0.8),
                ]
            )
            real_y.append(int(o["outcome_label"]))

        X = np.vstack([X_syn, np.array(real_X)])
        y = np.concatenate([y_syn, np.array(real_y)])

        X_scaled = self._scaler.fit_transform(X)
        self._model.fit(X_scaled, y)
        self._trained = True
        self._trained_on_real = True
        return True

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

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

        now = datetime.now()
        time_of_day = now.hour + now.minute / 60.0
        day_of_week = now.weekday()

        rows = []
        distances = []
        for driver in drivers:
            dist = _haversine_km(rider_lat, rider_lng, driver.lat, driver.lng)
            distances.append(dist)
            rows.append(
                [
                    dist,
                    driver.rating,
                    1.0 if driver.available else 0.0,
                    time_of_day,
                    day_of_week,
                    0.85,  # default acceptance rate until we have history
                ]
            )

        X = np.array(rows)
        X_scaled = self._scaler.transform(X)
        proba = self._model.predict_proba(X_scaled)[:, 1]

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
        """Return the best available driver for the given rider location."""
        available = self._drivers_service.get_available_drivers()
        if not available:
            raise ValueError("No available drivers at this time.")

        scored = self.score_drivers(rider_lat, rider_lng, available)
        best_driver, confidence, distance_km = scored[0]

        # ETA: assume average speed of 20 km/h in Lahore traffic
        eta_minutes = max(1, round((distance_km / 20.0) * 60))

        explanation = (
            f"AI selected {best_driver.name}: {distance_km:.1f} km away, "
            f"{best_driver.rating:.1f}★ rating, "
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

    @property
    def is_trained_on_real_data(self) -> bool:
        """True if the model has been retrained on real outcomes."""
        return getattr(self, "_trained_on_real", False)
