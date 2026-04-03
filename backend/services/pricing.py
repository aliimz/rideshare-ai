from backend.models.schemas import PriceResult


class DynamicPricingService:
    """Calculates dynamic ride fares with surge pricing in PKR."""

    BASE_RATE_PKR = 50.0          # flat booking fee
    PER_KM_RATE_PKR = 25.0        # rate per kilometer
    MIN_SURGE = 1.0
    MAX_SURGE = 2.5

    def calculate_price(self, distance_km: float, demand_level: float) -> PriceResult:
        """
        Calculate total fare.

        Args:
            distance_km: Trip distance in kilometres (must be > 0).
            demand_level: Current area demand from 0.0 (low) to 1.0 (very high).

        Returns:
            PriceResult with full cost breakdown.
        """
        # Clamp demand_level defensively
        demand_level = max(0.0, min(1.0, demand_level))

        base_fare = self.BASE_RATE_PKR + (distance_km * self.PER_KM_RATE_PKR)

        # Linear surge between MIN_SURGE and MAX_SURGE
        surge_multiplier = self.MIN_SURGE + (demand_level * (self.MAX_SURGE - self.MIN_SURGE))
        surge_multiplier = round(surge_multiplier, 2)

        surge_fee = base_fare * (surge_multiplier - 1.0)
        total = base_fare * surge_multiplier

        breakdown = {
            "booking_fee_pkr": round(self.BASE_RATE_PKR, 2),
            "distance_fee_pkr": round(distance_km * self.PER_KM_RATE_PKR, 2),
            "base_fare_pkr": round(base_fare, 2),
            "surge_fee_pkr": round(surge_fee, 2),
            "surge_multiplier": surge_multiplier,
            "demand_level": demand_level,
            "total_pkr": round(total, 2),
            "currency": "PKR",
        }

        return PriceResult(
            base_fare=round(base_fare, 2),
            surge_multiplier=surge_multiplier,
            total=round(total, 2),
            breakdown=breakdown,
        )
