from datetime import UTC, datetime
from typing import Self

import settings


class Shipment:
    def __init__(self, origin: str, weight_kg: float, *, fragile: bool = False) -> None: ...

    @classmethod
    def from_origin(cls, origin: str, weight_kg: float, *, fragile: bool = False) -> Self: ...

    @classmethod
    def from_hub(cls, weight_kg: float, *, fragile: bool = False) -> Self:
        return cls.from_origin(settings.home_depot, weight_kg, fragile=fragile)


class ScaleReading:
    def __init__(self, units: str, grams: int, scale_id: str) -> None: ...


# look-alike: public factory, not a private wrapper
def metric_reading(grams: int, scale_id: str) -> ScaleReading:
    return ScaleReading("metric", grams, scale_id)


# look-alike: pure pass-through, nothing pre-filled
def _ship(origin: str, weight_kg: float) -> Shipment:
    return Shipment.from_origin(origin, weight_kg)


# look-alike: third-party class, cannot grow a classmethod
def _now() -> datetime:
    return datetime.now(UTC)


# look-alike: the leading argument is derived from the parameters
def _reading_in(units: str, grams: int) -> ScaleReading:
    return ScaleReading(units.lower(), grams, "bench")


# look-alike: does more than forward
def _logged_shipment(weight_kg: float) -> Shipment:
    print("booking hub shipment")
    return Shipment.from_origin(settings.home_depot, weight_kg)
