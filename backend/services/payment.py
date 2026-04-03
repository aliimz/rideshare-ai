"""
PaymentService — fare calculation and simulated payment processing.

All monetary values are in Pakistani Rupees (PKR).
In this demo, process_payment always succeeds — swap the _simulate_charge
method for a real payment gateway in production.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# Fare constants (PKR)
# ---------------------------------------------------------------------------

_BASE_RATE_PKR: float = 50.0       # flat booking fee
_PER_KM_RATE_PKR: float = 25.0     # per-kilometre charge
_CURRENCY: str = "PKR"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_payment(
    payment_id: str,
    ride_id: str,
    amount: float,
) -> dict:
    """Return a fresh Payment dict in the 'pending' state."""
    return {
        "id":         payment_id,
        "ride_id":    ride_id,
        "amount":     round(amount, 2),
        "currency":   _CURRENCY,
        "status":     "pending",
        "created_at": _now_iso(),
        "paid_at":    None,
    }


# ---------------------------------------------------------------------------
# PaymentService
# ---------------------------------------------------------------------------

class PaymentService:
    """
    Simulated payment service.

    Payment dict schema
    -------------------
    id         : str       — UUID
    ride_id    : str
    amount     : float     — total in PKR
    currency   : str       — always "PKR"
    status     : str       — "pending" | "paid" | "failed"
    created_at : str       — ISO-8601 UTC
    paid_at    : str | None
    """

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate_fare(
        self,
        distance_km: float,
        surge_multiplier: float = 1.0,
    ) -> dict:
        """
        Calculate the full fare breakdown for a ride.

        Args:
            distance_km:      Trip distance in kilometres (must be > 0).
            surge_multiplier: Surge factor (>= 1.0; values below 1.0 are clamped).

        Returns:
            Dict with keys: base, surge_charge, total, currency.

        Raises:
            ValueError: If distance_km is not positive.
        """
        if distance_km <= 0:
            raise ValueError("distance_km must be greater than 0.")

        surge_multiplier = max(1.0, float(surge_multiplier))

        base = round(_BASE_RATE_PKR + (distance_km * _PER_KM_RATE_PKR), 2)
        surge_charge = round(base * (surge_multiplier - 1.0), 2)
        total = round(base + surge_charge, 2)

        return {
            "base":        base,
            "surge_charge": surge_charge,
            "total":       total,
            "currency":    _CURRENCY,
        }

    def create_payment(self, ride_id: str, amount: float) -> dict:
        """
        Create a new Payment record in the 'pending' state.

        Args:
            ride_id: ID of the associated ride.
            amount:  Total amount to charge (PKR).

        Returns:
            New Payment dict.

        Raises:
            ValueError: If ride_id is empty or amount is not positive.
        """
        if not ride_id or not isinstance(ride_id, str):
            raise ValueError("ride_id must be a non-empty string.")
        if amount <= 0:
            raise ValueError("amount must be greater than 0.")

        payment_id = str(uuid.uuid4())
        payment = _build_payment(payment_id, ride_id, amount)
        self._store[payment_id] = payment
        return dict(payment)

    def process_payment(self, payment_id: str) -> dict:
        """
        Simulate charging the rider (always succeeds in demo mode).

        Transitions the payment from 'pending' to 'paid' and records
        the timestamp.

        Args:
            payment_id: ID of the payment to process.

        Returns:
            Updated Payment dict.

        Raises:
            KeyError:   If payment_id is not found.
            ValueError: If the payment has already been processed.
        """
        payment = self._get_mutable(payment_id)

        if payment["status"] != "pending":
            raise ValueError(
                f"Payment '{payment_id}' is already in '{payment['status']}' state."
            )

        # Simulate charge — always succeeds in this demo
        updated = {
            **payment,
            "status":  "paid",
            "paid_at": _now_iso(),
        }
        self._store[payment_id] = updated
        return dict(updated)

    def get_payment(self, payment_id: str) -> dict:
        """
        Return a Payment dict by ID.

        Raises:
            KeyError: If payment_id is not found.
        """
        payment = self._store.get(payment_id)
        if payment is None:
            raise KeyError(f"Payment '{payment_id}' not found.")
        return dict(payment)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_mutable(self, payment_id: str) -> dict:
        payment = self._store.get(payment_id)
        if payment is None:
            raise KeyError(f"Payment '{payment_id}' not found.")
        return payment
