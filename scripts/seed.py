"""
Demo data seeder for RideShare AI.

Creates:
  - 20 demo drivers (User + Driver records)
  - 3 demo rider accounts
  - 50 historical completed rides

Run directly:
    python -m scripts.seed

Or called from main.py startup if the DB is empty.
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import hash_password
from backend.db.database import AsyncSessionLocal
from backend.db.models import Driver, Payment, PaymentStatus, Ride, RideStatus, User, UserRole

# ---------------------------------------------------------------------------
# Demo driver data (matches the existing DriversService hardcoded list)
# ---------------------------------------------------------------------------

_DEMO_DRIVERS = [
    ("asad.raza@demo.com",     "Asad Raza",      31.5204, 74.3587, 4.8, True,  "sedan",   512),
    ("bilal.sheikh@demo.com",  "Bilal Sheikh",   31.5232, 74.3621, 4.5, True,  "bike",    287),
    ("usman.q@demo.com",       "Usman Qureshi",  31.5180, 74.3553, 4.9, False, "sedan",   741),
    ("tariq.m@demo.com",       "Tariq Mahmood",  31.5251, 74.3648, 4.2, True,  "suv",     198),
    ("imran.ali@demo.com",     "Imran Ali",      31.5195, 74.3609, 4.7, True,  "sedan",   334),
    ("faisal.h@demo.com",      "Faisal Hussain", 31.5219, 74.3541, 3.9, False, "bike",    156),
    ("kamran.b@demo.com",      "Kamran Baig",    31.5170, 74.3634, 4.6, True,  "sedan",   422),
    ("zubair.a@demo.com",      "Zubair Ansari",  31.5243, 74.3596, 4.4, True,  "van",     603),
    ("naveed.k@demo.com",      "Naveed Khan",    31.5188, 74.3671, 4.1, False, "bike",    89),
    ("saeed.m@demo.com",       "Saeed Mirza",    31.5260, 74.3574, 5.0, True,  "sedan",   876),
    ("rashid.f@demo.com",      "Rashid Farooq",  31.5174, 74.3618, 4.3, True,  "sedan",   241),
    ("owais.s@demo.com",       "Owais Siddiqui", 31.5228, 74.3657, 4.7, False, "bike",    312),
    ("hamid.j@demo.com",       "Hamid Joiya",    31.5202, 74.3549, 3.8, True,  "suv",     167),
    ("adeel.b@demo.com",       "Adeel Butt",     31.5215, 74.3636, 4.5, True,  "sedan",   458),
    ("waqas.m@demo.com",       "Waqas Memon",    31.5156, 74.3601, 4.8, True,  "bike",    293),
    ("junaid.a@demo.com",      "Junaid Akhtar",  31.5237, 74.3526, 4.6, False, "luxury",  134),
    ("danish.l@demo.com",      "Danish Lodhi",   31.5183, 74.3686, 4.9, True,  "sedan",   567),
    ("shakeel.b@demo.com",     "Shakeel Baloch", 31.5248, 74.3613, 4.0, True,  "van",     203),
    ("pervaiz.g@demo.com",     "Pervaiz Gul",    31.5165, 74.3556, 4.4, False, "bike",    78),
    ("aamir.s@demo.com",       "Aamir Sohail",   31.5222, 74.3631, 4.7, True,  "sedan",   389),
]

_DEMO_RIDERS = [
    ("demo@rider.com",  "Demo Rider",  "03001234567"),
    ("test@rider.com",  "Test Rider",  "03009876543"),
    ("admin@rider.com", "Admin Rider", "03005551234"),
]

# Lahore pickup/dropoff zones for realistic ride data
_LAHORE_ZONES = [
    (31.5204, 74.3587, "Mall Road, Lahore"),
    (31.5120, 74.3290, "Gulberg III, Lahore"),
    (31.4697, 74.3936, "DHA Phase 5, Lahore"),
    (31.4700, 74.2800, "Johar Town, Lahore"),
    (31.5216, 74.4036, "Allama Iqbal Airport, Lahore"),
    (31.4840, 74.3180, "Model Town, Lahore"),
    (31.5140, 74.3380, "Liberty Market, Lahore"),
    (31.5430, 74.3290, "Cantt, Lahore"),
    (31.5060, 74.3220, "Garden Town, Lahore"),
    (31.4930, 74.2980, "Iqbal Town, Lahore"),
]


async def seed(session: AsyncSession) -> None:
    """Insert all demo data. Safe to call multiple times — checks first."""
    # ── Create driver users ────────────────────────────────────────────────
    driver_records: list[Driver] = []
    driver_password_hash = hash_password("Driver@123")

    for email, full_name, lat, lng, rating, available, vehicle_type, total_trips in _DEMO_DRIVERS:
        user = User(
            email=email,
            password_hash=driver_password_hash,
            full_name=full_name,
            phone="030" + str(random.randint(10000000, 99999999)),
            role=UserRole.driver,
        )
        session.add(user)
        await session.flush()

        driver = Driver(
            user_id=user.id,
            lat=lat,
            lng=lng,
            rating=rating,
            available=available,
            vehicle_type=vehicle_type,
            total_trips=total_trips,
            is_active=True,
        )
        session.add(driver)
        await session.flush()
        driver_records.append(driver)

    # ── Create rider users ─────────────────────────────────────────────────
    rider_password_hash = hash_password("Rider@123")
    rider_records: list[User] = []

    for email, full_name, phone in _DEMO_RIDERS:
        user = User(
            email=email,
            password_hash=rider_password_hash,
            full_name=full_name,
            phone=phone,
            role=UserRole.rider,
        )
        session.add(user)
        await session.flush()
        rider_records.append(user)

    # ── Create 50 historical completed rides ───────────────────────────────
    now = datetime.now(timezone.utc)

    for i in range(50):
        rider = random.choice(rider_records)
        driver = random.choice(driver_records)

        pickup = random.choice(_LAHORE_ZONES)
        dropoff = random.choice([z for z in _LAHORE_ZONES if z != pickup])

        days_ago = random.randint(1, 30)
        requested_at = now - timedelta(days=days_ago, hours=random.randint(0, 23))
        matched_at = requested_at + timedelta(minutes=random.randint(2, 5))
        completed_at = matched_at + timedelta(minutes=random.randint(10, 45))

        distance_km = round(random.uniform(2.0, 18.0), 1)
        surge = random.choice([1.0, 1.0, 1.0, 1.2, 1.5])
        fare = round((50 + distance_km * 25) * surge, 2)

        ride = Ride(
            rider_id=rider.id,
            driver_id=driver.id,
            status=RideStatus.completed,
            pickup_lat=pickup[0],
            pickup_lng=pickup[1],
            dropoff_lat=dropoff[0],
            dropoff_lng=dropoff[1],
            pickup_address=pickup[2],
            dropoff_address=dropoff[2],
            fare_amount=fare,
            surge_multiplier=surge,
            distance_km=distance_km,
            requested_at=requested_at,
            matched_at=matched_at,
            completed_at=completed_at,
        )
        session.add(ride)
        await session.flush()

        payment = Payment(
            ride_id=ride.id,
            amount=fare,
            status=PaymentStatus.paid,
            created_at=completed_at,
        )
        session.add(payment)

    await session.commit()
    print(
        f"[seed] Seeded {len(_DEMO_DRIVERS)} drivers, "
        f"{len(_DEMO_RIDERS)} riders, 50 historical rides."
    )


async def run() -> None:
    async with AsyncSessionLocal() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(run())
