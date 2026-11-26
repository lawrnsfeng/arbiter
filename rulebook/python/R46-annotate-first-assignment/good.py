from dataclasses import dataclass, field
from enum import Enum
from typing import ClassVar


def average_rainfall(readings: list[tuple[str, float]]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for station, millimetres in readings:  # loop targets cannot carry an annotation
        totals[station] = totals.get(station, 0.0) + millimetres
    count: int = len(readings)
    count = count or 1
    return {k: v / count for k, v in totals.items()}


def scale(values: list[float], factor: float) -> list[float]:
    factor = factor or 1.0  # a parameter is already stated
    low, high = min(values), max(values)  # tuple targets cannot be annotated
    peak: float
    peak = high
    low = low * factor  # rebinding a tuple-bound name
    return [v * factor for v in values if low <= v <= peak]


def last_station(path: str) -> str:
    for line in open(path):
        pass
    line = line.strip()  # rebinding a loop-bound name
    with open(path) as log:
        log = None  # rebinding a `with ... as` name
    return line


class Sky(Enum):
    CLEAR = "clear"  # enum members must not be annotated
    OVERCAST = "overcast"


class Thermometer:
    __slots__ = ("offset",)
    unit: str = "celsius"
    unit = "kelvin"  # already stated above


@dataclass
class StationReport:
    MAX_GUST_KMH: ClassVar[float] = 250.0
    station: str
    gusts: list[float] = field(default_factory=list)
