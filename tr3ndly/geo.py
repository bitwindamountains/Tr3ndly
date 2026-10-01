from dataclasses import dataclass
from datetime import timedelta, timezone

# The Philippines has no daylight saving time, so a fixed offset is exact and needs no tzdata.
MANILA = timezone(timedelta(hours=8), "PHT")


@dataclass(frozen=True)
class MonitoredLocation:
    slug: str
    name: str
    latitude: float
    longitude: float
    # Relative audience reach, 0-100, used by the timely score.
    reach: int


PH_LOCATIONS: tuple[MonitoredLocation, ...] = (
    MonitoredLocation("metro-manila", "Metro Manila", 14.5995, 120.9842, reach=100),
    MonitoredLocation("cebu-city", "Cebu City", 10.3157, 123.8854, reach=60),
    MonitoredLocation("davao-city", "Davao City", 7.1907, 125.4553, reach=55),
)

LOCATIONS_BY_NAME = {location.name: location for location in PH_LOCATIONS}
