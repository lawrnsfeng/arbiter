from dataclasses import asdict, dataclass
from datetime import datetime

RAIN_BELOW_CELSIUS = 5


@dataclass(frozen=True)
class Reading:
    station: str
    celsius: float
    taken_at: datetime

    def as_dict(self) -> dict[str, object]:
        return {"station": self.station, "celsius": self.celsius, "taken_at": self.taken_at.isoformat()}

    def to_row(self) -> dict[str, object]:
        return {"station": self.station, "celsius": self.celsius}

    @classmethod
    def from_sensor(cls, station, sensor) -> "Reading":
        return cls(station.name, sensor.read(), sensor.clock())


ByStation = dict[str, Reading]


def by_station(readings: list[Reading]) -> dict[str, Reading]:
    return {r.station: r for r in readings}


def counts(readings: list[Reading]) -> dict[str, int]:
    totals = {"rain": 0, "dry": 0}
    for r in readings:
        totals["rain" if r.celsius < RAIN_BELOW_CELSIUS else "dry"] += 1
    return dict(totals)


def labelled(reading: Reading, unit: str) -> dict[str, object]:
    return {**asdict(reading), "unit": unit}


def keyed(reading: Reading) -> dict[str, float]:
    return {reading.station: reading.celsius}


def single(reading: Reading) -> dict[str, float]:
    return {"celsius": reading.celsius}
