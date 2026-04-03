from typing import List
from backend.models.schemas import Driver


class DriversService:
    """Provides a hardcoded list of 20 drivers with realistic Lahore coordinates."""

    _drivers: List[Driver] = [
        Driver(id=1,  name="Asad Raza",       lat=31.5204, lng=74.3587, rating=4.8, available=True,  vehicle_type="car"),
        Driver(id=2,  name="Bilal Sheikh",    lat=31.5232, lng=74.3621, rating=4.5, available=True,  vehicle_type="bike"),
        Driver(id=3,  name="Usman Qureshi",   lat=31.5180, lng=74.3553, rating=4.9, available=False, vehicle_type="car"),
        Driver(id=4,  name="Tariq Mahmood",   lat=31.5251, lng=74.3648, rating=4.2, available=True,  vehicle_type="rickshaw"),
        Driver(id=5,  name="Imran Ali",       lat=31.5195, lng=74.3609, rating=4.7, available=True,  vehicle_type="car"),
        Driver(id=6,  name="Faisal Hussain",  lat=31.5219, lng=74.3541, rating=3.9, available=False, vehicle_type="bike"),
        Driver(id=7,  name="Kamran Baig",     lat=31.5170, lng=74.3634, rating=4.6, available=True,  vehicle_type="car"),
        Driver(id=8,  name="Zubair Ansari",   lat=31.5243, lng=74.3596, rating=4.4, available=True,  vehicle_type="rickshaw"),
        Driver(id=9,  name="Naveed Khan",     lat=31.5188, lng=74.3671, rating=4.1, available=False, vehicle_type="bike"),
        Driver(id=10, name="Saeed Mirza",     lat=31.5260, lng=74.3574, rating=5.0, available=True,  vehicle_type="car"),
        Driver(id=11, name="Rashid Farooq",   lat=31.5174, lng=74.3618, rating=4.3, available=True,  vehicle_type="car"),
        Driver(id=12, name="Owais Siddiqui",  lat=31.5228, lng=74.3657, rating=4.7, available=False, vehicle_type="bike"),
        Driver(id=13, name="Hamid Joiya",     lat=31.5202, lng=74.3549, rating=3.8, available=True,  vehicle_type="rickshaw"),
        Driver(id=14, name="Adeel Butt",      lat=31.5215, lng=74.3636, rating=4.5, available=True,  vehicle_type="car"),
        Driver(id=15, name="Waqas Memon",     lat=31.5156, lng=74.3601, rating=4.8, available=True,  vehicle_type="bike"),
        Driver(id=16, name="Junaid Akhtar",   lat=31.5237, lng=74.3526, rating=4.6, available=False, vehicle_type="car"),
        Driver(id=17, name="Danish Lodhi",    lat=31.5183, lng=74.3686, rating=4.9, available=True,  vehicle_type="car"),
        Driver(id=18, name="Shakeel Baloch",  lat=31.5248, lng=74.3613, rating=4.0, available=True,  vehicle_type="rickshaw"),
        Driver(id=19, name="Pervaiz Gul",     lat=31.5165, lng=74.3556, rating=4.4, available=False, vehicle_type="bike"),
        Driver(id=20, name="Aamir Sohail",    lat=31.5222, lng=74.3631, rating=4.7, available=True,  vehicle_type="car"),
    ]

    def get_all_drivers(self) -> List[Driver]:
        """Return a new list of all drivers (immutable — callers get a copy)."""
        return list(self._drivers)

    def get_available_drivers(self) -> List[Driver]:
        """Return only available drivers."""
        return [d for d in self._drivers if d.available]
