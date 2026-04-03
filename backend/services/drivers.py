from typing import List
from backend.models.schemas import Driver


class DriversService:
    """Provides a hardcoded list of 20 drivers with realistic Karachi coordinates."""

    _drivers: List[Driver] = [
        Driver(id=1,  name="Asad Raza",       lat=24.8607, lng=67.0011, rating=4.8, available=True,  vehicle_type="car"),
        Driver(id=2,  name="Bilal Sheikh",    lat=24.8632, lng=67.0045, rating=4.5, available=True,  vehicle_type="bike"),
        Driver(id=3,  name="Usman Qureshi",   lat=24.8580, lng=66.9987, rating=4.9, available=False, vehicle_type="car"),
        Driver(id=4,  name="Tariq Mahmood",   lat=24.8651, lng=67.0072, rating=4.2, available=True,  vehicle_type="rickshaw"),
        Driver(id=5,  name="Imran Ali",       lat=24.8595, lng=67.0033, rating=4.7, available=True,  vehicle_type="car"),
        Driver(id=6,  name="Faisal Hussain",  lat=24.8619, lng=66.9965, rating=3.9, available=False, vehicle_type="bike"),
        Driver(id=7,  name="Kamran Baig",     lat=24.8570, lng=67.0058, rating=4.6, available=True,  vehicle_type="car"),
        Driver(id=8,  name="Zubair Ansari",   lat=24.8643, lng=67.0020, rating=4.4, available=True,  vehicle_type="rickshaw"),
        Driver(id=9,  name="Naveed Khan",     lat=24.8588, lng=67.0095, rating=4.1, available=False, vehicle_type="bike"),
        Driver(id=10, name="Saeed Mirza",     lat=24.8660, lng=66.9998, rating=5.0, available=True,  vehicle_type="car"),
        Driver(id=11, name="Rashid Farooq",   lat=24.8574, lng=67.0042, rating=4.3, available=True,  vehicle_type="car"),
        Driver(id=12, name="Owais Siddiqui",  lat=24.8628, lng=67.0081, rating=4.7, available=False, vehicle_type="bike"),
        Driver(id=13, name="Hamid Joiya",     lat=24.8602, lng=66.9973, rating=3.8, available=True,  vehicle_type="rickshaw"),
        Driver(id=14, name="Adeel Butt",      lat=24.8615, lng=67.0060, rating=4.5, available=True,  vehicle_type="car"),
        Driver(id=15, name="Waqas Memon",     lat=24.8556, lng=67.0025, rating=4.8, available=True,  vehicle_type="bike"),
        Driver(id=16, name="Junaid Akhtar",   lat=24.8637, lng=66.9950, rating=4.6, available=False, vehicle_type="car"),
        Driver(id=17, name="Danish Lodhi",    lat=24.8583, lng=67.0110, rating=4.9, available=True,  vehicle_type="car"),
        Driver(id=18, name="Shakeel Baloch",  lat=24.8648, lng=67.0037, rating=4.0, available=True,  vehicle_type="rickshaw"),
        Driver(id=19, name="Pervaiz Gul",     lat=24.8565, lng=66.9980, rating=4.4, available=False, vehicle_type="bike"),
        Driver(id=20, name="Aamir Sohail",    lat=24.8622, lng=67.0055, rating=4.7, available=True,  vehicle_type="car"),
    ]

    def get_all_drivers(self) -> List[Driver]:
        """Return a new list of all drivers (immutable — callers get a copy)."""
        return list(self._drivers)

    def get_available_drivers(self) -> List[Driver]:
        """Return only available drivers."""
        return [d for d in self._drivers if d.available]
