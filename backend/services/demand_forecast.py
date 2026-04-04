"""
XGBoost demand forecasting service.

Predicts demand_level (0.0-1.0) for any lat/lng and time by learning from
historical ride patterns in the database.
"""

import math
from datetime import datetime
from typing import Optional

import numpy as np
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from backend.db.database import AsyncSessionLocal
from backend.db.models import Driver, Ride, RideStatus
from sqlalchemy import func, select


class DemandForecastService:
    """
    ML-powered demand forecasting using XGBoost.

    Features:
        - hour, day_of_week          : temporal patterns
        - lat_bin, lng_bin           : 1.1km geospatial grid
        - available_drivers          : current supply
        - active_rides               : current demand proxy
        - historical_avg_demand      : baseline for that grid/hour
    """

    GRID_SIZE = 0.01  # ~1.1 km in Lahore latitude

    def __init__(self) -> None:
        self._model: Optional[XGBRegressor] = None
        self._scaler = StandardScaler()
        self._trained = False
        self._feature_cols = [
            "hour",
            "day_of_week",
            "lat_bin",
            "lng_bin",
            "available_drivers",
            "active_rides",
            "historical_avg_demand",
        ]

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    async def generate_training_data(self) -> tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Build X, y from historical rides. Returns (None, None) if insufficient data."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Ride).where(Ride.status == RideStatus.completed)
            )
            rides = list(result.scalars().all())

            if len(rides) < 10:
                return None, None

            # Build grid-level aggregates
            grid_counts: dict[tuple[float, float, int, int], dict] = {}
            for ride in rides:
                dt = ride.requested_at
                if dt is None:
                    continue
                lat_bin = self._bin(ride.pickup_lat)
                lng_bin = self._bin(ride.pickup_lng)
                key = (lat_bin, lng_bin, dt.hour, dt.weekday())
                grid_counts.setdefault(key, {"count": 0, "surge_sum": 0.0})
                grid_counts[key]["count"] += 1
                grid_counts[key]["surge_sum"] += float(ride.surge_multiplier or 1.0)

            if not grid_counts:
                return None, None

            max_count = max(v["count"] for v in grid_counts.values())

            rows = []
            labels = []
            rng = np.random.default_rng(42)
            for key, stats in grid_counts.items():
                lat_bin, lng_bin, hour, dow = key
                demand_level = stats["count"] / max_count
                # Synthetic supply/demand context for training
                available_drivers = int(rng.poisson(lam=12))
                active_rides = int(rng.poisson(lam=stats["count"]))
                rows.append([
                    hour,
                    dow,
                    lat_bin,
                    lng_bin,
                    available_drivers,
                    active_rides,
                    demand_level,
                ])
                labels.append(demand_level)

            return np.array(rows, dtype=np.float32), np.array(labels, dtype=np.float32)

    def train(self, X: np.ndarray, y: np.ndarray) -> bool:
        """Fit the XGBoost model. Returns True on success."""
        if len(X) < 10:
            return False
        self._scaler.fit(X)
        X_scaled = self._scaler.transform(X)
        self._model = XGBRegressor(
            n_estimators=120,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=2,
        )
        self._model.fit(X_scaled, y)
        self._trained = True
        return True

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(
        self,
        lat: float,
        lng: float,
        dt: datetime,
        available_drivers: int,
        active_rides: int,
    ) -> float:
        """Return predicted demand_level between 0.0 and 1.0."""
        if not self._trained or self._model is None:
            return self._heuristic_predict(dt, available_drivers, active_rides)

        lat_bin = self._bin(lat)
        lng_bin = self._bin(lng)
        hist = 0.5  # fallback baseline; could be queried from DB

        X = np.array(
            [[dt.hour, dt.weekday(), lat_bin, lng_bin, available_drivers, active_rides, hist]],
            dtype=np.float32,
        )
        X_scaled = self._scaler.transform(X)
        pred = float(self._model.predict(X_scaled)[0])
        return float(np.clip(pred, 0.0, 1.0))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _bin(self, val: float) -> float:
        return round(val / self.GRID_SIZE) * self.GRID_SIZE

    def _heuristic_predict(self, dt: datetime, available_drivers: int, active_rides: int) -> float:
        """Rule-based fallback when ML model is not ready."""
        hour = dt.hour
        base = 0.25

        # Rush-hour peaks
        if hour in {8, 9, 13, 14, 18, 19, 20}:
            base += 0.35
        elif hour in {12, 17, 21}:
            base += 0.20

        # Weekend nightlife
        if dt.weekday() >= 5 and hour >= 22:
            base += 0.15

        # Supply-demand ratio
        ratio = active_rides / max(available_drivers, 1)
        base += min(ratio * 0.30, 0.30)

        return float(min(base, 1.0))
