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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.security import hash_password
from backend.db.database import AsyncSessionLocal
from backend.db.models import Driver, MatchOutcome, Payment, PaymentStatus, Ride, RideStatus, User, UserRole

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

_LIVE_RIDE_TEMPLATES = [
    (_LAHORE_ZONES[0], _LAHORE_ZONES[2], 1.2),
    (_LAHORE_ZONES[6], _LAHORE_ZONES[4], 1.0),
    (_LAHORE_ZONES[3], _LAHORE_ZONES[1], 1.1),
    (_LAHORE_ZONES[8], _LAHORE_ZONES[5], 1.3),
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

    # ── Seed match outcomes for ML retraining ───────────────────────────────
    await _seed_match_outcomes(session, driver_records)

    await session.commit()
    print(
        f"[seed] Seeded {len(_DEMO_DRIVERS)} drivers, "
        f"{len(_DEMO_RIDERS)} riders, 50 historical rides, match outcomes."
    )


async def ensure_demo_runtime_data(session: AsyncSession) -> None:
    """
    Ensure the database has a few live rides and some revenue today.

    This runs on every startup but only inserts data when the live/demo
    records are missing, so the admin and driver dashboards stay useful.
    """
    rides_result = await session.execute(select(Ride))
    all_rides = list(rides_result.scalars().all())

    users_result = await session.execute(
        select(User).where(User.role == UserRole.rider).order_by(User.id.asc())
    )
    riders = list(users_result.scalars().all())

    drivers_result = await session.execute(select(Driver).order_by(Driver.id.asc()))
    drivers = list(drivers_result.scalars().all())

    if not riders or not drivers:
        return

    active_statuses = {
        RideStatus.requested,
        RideStatus.matched,
        RideStatus.en_route,
        RideStatus.arrived,
        RideStatus.in_progress,
    }
    has_live_rides = any(ride.status in active_statuses for ride in all_rides)

    now = datetime.now(timezone.utc)
    completed_today = [
        ride
        for ride in all_rides
        if ride.status == RideStatus.completed
        and ride.completed_at is not None
        and ride.completed_at.date() == now.date()
    ]

    if not has_live_rides:
        for index, (pickup, dropoff, surge) in enumerate(_LIVE_RIDE_TEMPLATES):
            rider = riders[index % len(riders)]
            distance_km = _estimate_distance_km(pickup[0], pickup[1], dropoff[0], dropoff[1])
            fare = _estimate_fare(distance_km, surge)
            requested_at = now - timedelta(minutes=10 + index * 6)

            session.add(
                Ride(
                    rider_id=rider.id,
                    status=RideStatus.requested,
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
                )
            )

        live_driver = next((driver for driver in drivers if driver.available), drivers[0])
        live_driver.available = False
        matched_pickup = _LAHORE_ZONES[7]
        matched_dropoff = _LAHORE_ZONES[4]
        matched_distance = _estimate_distance_km(
            matched_pickup[0],
            matched_pickup[1],
            matched_dropoff[0],
            matched_dropoff[1],
        )
        session.add(
            Ride(
                rider_id=riders[0].id,
                driver_id=live_driver.id,
                status=RideStatus.en_route,
                pickup_lat=matched_pickup[0],
                pickup_lng=matched_pickup[1],
                dropoff_lat=matched_dropoff[0],
                dropoff_lng=matched_dropoff[1],
                pickup_address=matched_pickup[2],
                dropoff_address=matched_dropoff[2],
                fare_amount=_estimate_fare(matched_distance, 1.15),
                surge_multiplier=1.15,
                distance_km=matched_distance,
                requested_at=now - timedelta(minutes=18),
                matched_at=now - timedelta(minutes=12),
            )
        )

        in_progress_driver = next(
            (driver for driver in drivers if driver.available and driver.id != live_driver.id),
            drivers[min(1, len(drivers) - 1)],
        )
        in_progress_driver.available = False
        in_progress_pickup = _LAHORE_ZONES[1]
        in_progress_dropoff = _LAHORE_ZONES[9]
        in_progress_distance = _estimate_distance_km(
            in_progress_pickup[0],
            in_progress_pickup[1],
            in_progress_dropoff[0],
            in_progress_dropoff[1],
        )
        session.add(
            Ride(
                rider_id=riders[1 % len(riders)].id,
                driver_id=in_progress_driver.id,
                status=RideStatus.in_progress,
                pickup_lat=in_progress_pickup[0],
                pickup_lng=in_progress_pickup[1],
                dropoff_lat=in_progress_dropoff[0],
                dropoff_lng=in_progress_dropoff[1],
                pickup_address=in_progress_pickup[2],
                dropoff_address=in_progress_dropoff[2],
                fare_amount=_estimate_fare(in_progress_distance, 1.0),
                surge_multiplier=1.0,
                distance_km=in_progress_distance,
                requested_at=now - timedelta(minutes=35),
                matched_at=now - timedelta(minutes=28),
            )
        )

    if len(completed_today) < 3:
        needed = 3 - len(completed_today)
        for index in range(needed):
            rider = riders[index % len(riders)]
            driver = drivers[(index + 2) % len(drivers)]
            pickup = _LAHORE_ZONES[(index + 2) % len(_LAHORE_ZONES)]
            dropoff = _LAHORE_ZONES[(index + 5) % len(_LAHORE_ZONES)]
            surge = [1.0, 1.1, 1.3][index % 3]
            distance_km = _estimate_distance_km(pickup[0], pickup[1], dropoff[0], dropoff[1])
            fare = _estimate_fare(distance_km, surge)

            requested_at = now - timedelta(hours=5 - index, minutes=15)
            matched_at = requested_at + timedelta(minutes=3)
            completed_at = matched_at + timedelta(minutes=18 + index * 4)

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

            session.add(
                Payment(
                    ride_id=ride.id,
                    amount=fare,
                    status=PaymentStatus.paid,
                    created_at=completed_at,
                )
            )

    await session.commit()


async def _seed_match_outcomes(session: AsyncSession, drivers: list[Driver]) -> None:
    """Generate synthetic match outcomes so the ML model has data to retrain on."""
    import random
    rng = random.Random(42)
    now = datetime.now(timezone.utc)

    for i in range(120):
        driver = rng.choice(drivers)
        distance_km = round(rng.uniform(0.5, 8.0), 2)
        rating = driver.rating
        available = 1.0 if driver.available else 0.0
        time_of_day = rng.uniform(0.0, 24.0)
        day_of_week = rng.randint(0, 6)
        acceptance = rng.uniform(0.6, 0.95)

        # Simulate outcome: closer + higher rating = more likely good
        score = (1.0 / (distance_km + 0.5)) * 2 + (rating - 3.5) * 1.5 + acceptance
        outcome_label = 1 if score > 2.5 else 0
        actual_rating = round(rng.uniform(4.0, 5.0), 1) if outcome_label else round(rng.uniform(2.5, 4.2), 1)
        wait_min = rng.uniform(3.0, 8.0) if outcome_label else rng.uniform(12.0, 25.0)
        cancelled = outcome_label == 0 and rng.random() < 0.3

        session.add(
            MatchOutcome(
                ride_id=None,
                driver_id=driver.id,
                rider_lat=round(rng.uniform(31.45, 31.55), 4),
                rider_lng=round(rng.uniform(74.25, 74.42), 4),
                distance_km=distance_km,
                driver_rating=rating,
                availability_score=available,
                time_of_day=time_of_day,
                day_of_week=day_of_week,
                driver_acceptance_rate=acceptance,
                matched_at=now - timedelta(days=rng.randint(1, 30), hours=rng.randint(0, 23)),
                outcome_label=0 if cancelled else outcome_label,
                actual_rating=actual_rating,
                cancelled=cancelled,
                actual_wait_minutes=round(wait_min, 1),
            )
        )


async def run() -> None:
    async with AsyncSessionLocal() as session:
        await seed(session)


if __name__ == "__main__":
    asyncio.run(run())


def _estimate_distance_km(
    pickup_lat: float,
    pickup_lng: float,
    dropoff_lat: float,
    dropoff_lng: float,
) -> float:
    """
    Approximate ride distance using a lightweight local formula.
    """
    lat_delta = (pickup_lat - dropoff_lat) * 111.0
    lng_delta = (pickup_lng - dropoff_lng) * 96.0
    return round((lat_delta ** 2 + lng_delta ** 2) ** 0.5, 2)


def _estimate_fare(distance_km: float, surge_multiplier: float) -> float:
    base_fare = 50 + (distance_km * 25)
    return round(base_fare * surge_multiplier, 2)
