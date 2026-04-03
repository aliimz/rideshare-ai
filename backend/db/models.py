"""
SQLAlchemy ORM models for the RideShare AI application.

Models
------
- User      — app users (riders and drivers)
- Driver    — driver-specific profile linked to a User
- Ride      — a single ride lifecycle
- Payment   — payment record associated with a Ride
"""

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.database import Base

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class UserRole(str, enum.Enum):
    rider = "rider"
    driver = "driver"


class RideStatus(str, enum.Enum):
    requested = "requested"
    matched = "matched"
    en_route = "en_route"
    arrived = "arrived"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------


class User(Base):
    """Application user — can be a rider or a driver."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", create_type=True),
        nullable=False,
        default=UserRole.rider,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    driver_profile: Mapped["Driver | None"] = relationship(
        "Driver", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    rides_as_rider: Mapped[list["Ride"]] = relationship(
        "Ride", foreign_keys="Ride.rider_id", back_populates="rider"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"


class Driver(Base):
    """Driver-specific profile — linked 1-to-1 with a User of role 'driver'."""

    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    vehicle_type: Mapped[str] = mapped_column(String(50), nullable=False, default="sedan")
    total_trips: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="driver_profile")
    rides: Mapped[list["Ride"]] = relationship(
        "Ride", foreign_keys="Ride.driver_id", back_populates="driver"
    )

    def __repr__(self) -> str:
        return f"<Driver id={self.id} user_id={self.user_id} available={self.available}>"


class Ride(Base):
    """A single ride from request through completion or cancellation."""

    __tablename__ = "rides"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rider_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    driver_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("drivers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[RideStatus] = mapped_column(
        Enum(RideStatus, name="ride_status", create_type=True),
        nullable=False,
        default=RideStatus.requested,
        index=True,
    )

    # Location
    pickup_lat: Mapped[float] = mapped_column(Float, nullable=False)
    pickup_lng: Mapped[float] = mapped_column(Float, nullable=False)
    dropoff_lat: Mapped[float] = mapped_column(Float, nullable=False)
    dropoff_lng: Mapped[float] = mapped_column(Float, nullable=False)

    # Fare
    fare_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    surge_multiplier: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    rider: Mapped["User"] = relationship(
        "User", foreign_keys=[rider_id], back_populates="rides_as_rider"
    )
    driver: Mapped["Driver | None"] = relationship(
        "Driver", foreign_keys=[driver_id], back_populates="rides"
    )
    payment: Mapped["Payment | None"] = relationship(
        "Payment", back_populates="ride", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Ride id={self.id} status={self.status} rider_id={self.rider_id}>"


class Payment(Base):
    """Payment record associated with a completed ride."""

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ride_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("rides.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", create_type=True),
        nullable=False,
        default=PaymentStatus.pending,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    ride: Mapped["Ride"] = relationship("Ride", back_populates="payment")

    def __repr__(self) -> str:
        return f"<Payment id={self.id} ride_id={self.ride_id} status={self.status}>"
