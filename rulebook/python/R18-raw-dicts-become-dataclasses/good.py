import json
from dataclasses import dataclass


@dataclass(frozen=True)
class Reading:
    station: str
    celsius: float

    @classmethod
    def from_record(cls, raw: dict[str, object]) -> "Reading":
        return cls(station=str(raw["station"]), celsius=float(raw["celsius"]))

    def to_record(self) -> dict[str, object]:
        return {"station": self.station, "celsius": self.celsius}


def load_readings(path: str) -> list[Reading]:
    with open(path) as fh:
        raw = json.load(fh)
    return [Reading.from_record(item) for item in raw]


def warmest(readings: list[Reading]) -> Reading:
    return max(readings, key=lambda r: r.celsius)


# Look-alike: a dict the function builds itself.
def tally(stations: list[str]) -> int:
    counts: dict[str, int] = {}
    counts["total"] = len(stations)
    return counts["total"]


# Look-alike: an integer index into a parsed list.
def first_entry(blob: bytes) -> object:
    return json.loads(blob)[0]
