"""
Repository layer — encapsulates all database access behind a clean interface.

Each repository receives an AsyncSession at construction time and exposes
typed, named methods so business logic never writes raw queries.

Repositories
------------
- UserRepository
- DriverRepository
- RideRepository
- PaymentRepository
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Driver, Payment, PaymentStatus, Ride, RideStatus, User


# ---------------------------------------------------------------------------
# UserRepository
# ---------------------------------------------------------------------------


class UserRepository:
    """CRUD operations for the User model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        full_name: str,
        phone: str | None = None,
        role: str = "rider",
    ) -> User:
        """Persist a new user and return the populated instance."""
        user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            phone=phone,
            role=role,  # type: ignore[arg-type]
        )
        self._session.add(user)
        await self._session.flush()   # Assign PK without committing
        await self._session.refresh(user)
        return user

    async def find_by_email(self, email: str) -> User | None:
        """Return the user with the given email, or None if not found."""
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def find_by_id(self, user_id: int) -> User | None:
        """Return the user with the given primary key, or None if not found."""
        return await self._session.get(User, user_id)


# ---------------------------------------------------------------------------
# DriverRepository
# ---------------------------------------------------------------------------


class DriverRepository:
    """CRUD and query operations for the Driver model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        user_id: int,
        lat: float | None = None,
        lng: float | None = None,
        vehicle_type: str = "sedan",
        rating: float = 5.0,
    ) -> Driver:
        """Create a new driver profile and return the populated instance."""
        driver = Driver(
            user_id=user_id,
            lat=lat,
            lng=lng,
            vehicle_type=vehicle_type,
            rating=rating,
        )
        self._session.add(driver)
        await self._session.flush()
        await self._session.refresh(driver)
        return driver

    async def get_all(self) -> list[Driver]:
        """Return all driver records regardless of availability."""
        result = await self._session.execute(select(Driver))
        return list(result.scalars().all())

    async def get_available(self) -> list[Driver]:
        """Return drivers that are active and currently marked available."""
        result = await self._session.execute(
            select(Driver).where(
                Driver.available.is_(True),
                Driver.is_active.is_(True),
            )
        )
        return list(result.scalars().all())

    async def update_location(
        self, driver_id: int, *, lat: float, lng: float
    ) -> Driver | None:
        """
        Update the GPS coordinates for a driver.

        Returns the updated Driver instance, or None if the driver does not exist.
        """
        await self._session.execute(
            update(Driver)
            .where(Driver.id == driver_id)
            .values(lat=lat, lng=lng)
        )
        await self._session.flush()
        return await self._session.get(Driver, driver_id)

    async def update_availability(
        self, driver_id: int, *, available: bool
    ) -> Driver | None:
        """
        Set the available flag for a driver.

        Returns the updated Driver instance, or None if the driver does not exist.
        """
        await self._session.execute(
            update(Driver)
            .where(Driver.id == driver_id)
            .values(available=available)
        )
        await self._session.flush()
        return await self._session.get(Driver, driver_id)


# ---------------------------------------------------------------------------
# RideRepository
# ---------------------------------------------------------------------------


class RideRepository:
    """CRUD and query operations for the Ride model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        rider_id: int,
        pickup_lat: float,
        pickup_lng: float,
        dropoff_lat: float,
        dropoff_lng: float,
        pickup_address: str | None = None,
        dropoff_address: str | None = None,
        fare_amount: float | None = None,
        surge_multiplier: float = 1.0,
        distance_km: float | None = None,
    ) -> Ride:
        """Persist a new ride in the 'requested' status and return the instance."""
        ride = Ride(
            rider_id=rider_id,
            pickup_lat=pickup_lat,
            pickup_lng=pickup_lng,
            dropoff_lat=dropoff_lat,
            dropoff_lng=dropoff_lng,
            pickup_address=pickup_address,
            dropoff_address=dropoff_address,
            fare_amount=fare_amount,
            surge_multiplier=surge_multiplier,
            distance_km=distance_km,
            status=RideStatus.requested,
        )
        self._session.add(ride)
        await self._session.flush()
        await self._session.refresh(ride)
        return ride

    async def update_status(
        self,
        ride_id: int,
        *,
        status: RideStatus,
        driver_id: int | None = None,
    ) -> Ride | None:
        """
        Transition a ride to a new status.

        Automatically records matched_at / completed_at timestamps on the
        relevant transitions.  Optionally assigns a driver when the status
        moves to 'matched'.

        Returns the updated Ride instance, or None if not found.
        """
        now = datetime.now(tz=timezone.utc)
        values: dict = {"status": status}

        if status == RideStatus.matched:
            values["matched_at"] = now
            if driver_id is not None:
                values["driver_id"] = driver_id

        if status in (RideStatus.completed, RideStatus.cancelled):
            values["completed_at"] = now

        await self._session.execute(
            update(Ride).where(Ride.id == ride_id).values(**values)
        )
        await self._session.flush()
        return await self._session.get(Ride, ride_id)

    async def find_by_id(self, ride_id: int) -> Ride | None:
        """Return the ride with the given primary key, or None if not found."""
        return await self._session.get(Ride, ride_id)

    async def get_rider_history(self, rider_id: int) -> list[Ride]:
        """Return all rides for a given rider, ordered most-recent first."""
        result = await self._session.execute(
            select(Ride)
            .where(Ride.rider_id == rider_id)
            .order_by(Ride.requested_at.desc())
        )
        return list(result.scalars().all())


# ---------------------------------------------------------------------------
# PaymentRepository
# ---------------------------------------------------------------------------


class PaymentRepository:
    """CRUD operations for the Payment model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        ride_id: int,
        amount: float,
        status: PaymentStatus = PaymentStatus.pending,
    ) -> Payment:
        """Create a payment record for a ride and return the populated instance."""
        payment = Payment(
            ride_id=ride_id,
            amount=amount,
            status=status,
        )
        self._session.add(payment)
        await self._session.flush()
        await self._session.refresh(payment)
        return payment

    async def update_status(
        self, payment_id: int, *, status: PaymentStatus
    ) -> Payment | None:
        """
        Update the status of an existing payment.

        Returns the updated Payment instance, or None if not found.
        """
        await self._session.execute(
            update(Payment)
            .where(Payment.id == payment_id)
            .values(status=status)
        )
        await self._session.flush()
        return await self._session.get(Payment, payment_id)
