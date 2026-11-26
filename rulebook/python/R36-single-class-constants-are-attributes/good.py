import dataclasses

from pydantic import TypeAdapter

from .stations import NORTH_CODE

SHARED_UNITS = "metric"
LOCAL_ONLY_LIMIT = 40
HISTORY_DAYS = 7
SLOTS = True


class GustFilter:
    MAX_GUST_KMH: int = 150
    SMOOTHING: float = 0.3

    def keep(self, reading) -> bool:
        return reading.gust <= self.MAX_GUST_KMH


# look-alike: read by two classes
class Report:
    def units(self) -> str:
        return SHARED_UNITS


class Chart:
    def axis(self) -> str:
        return SHARED_UNITS


# look-alike: read by a class and a module function
class History:
    def window(self) -> int:
        return HISTORY_DAYS


def trim(readings):
    return readings[-HISTORY_DAYS:]


# look-alike: read only at module level
CUTOFF = LOCAL_ONLY_LIMIT * 2


# look-alike: used in a decorator, which a class attribute cannot serve
@dataclasses.dataclass(slots=SLOTS)
class Reading:
    gust: float


# look-alike: imported from elsewhere, not defined here
class North:
    code: str = NORTH_CODE


# look-alike: built from the class that uses it, so it cannot be one of its attributes
@dataclasses.dataclass
class Gauge:
    station: str

    @classmethod
    def parse(cls, raw: bytes) -> "Gauge":
        return _GAUGE_ADAPTER.validate_json(raw)


_GAUGE_ADAPTER = TypeAdapter(Gauge)
