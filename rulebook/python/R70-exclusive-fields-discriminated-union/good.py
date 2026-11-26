from typing import Annotated, Literal

from pydantic import BeforeValidator, ConfigDict, Field, model_validator
from pydantic.dataclasses import dataclass

from depot.constants import LOCKER_SLOTS, MAX_HOME_DROPS


class LockerSlotOutOfRange(ValueError):
    """Raised for a locker slot outside the bank's 1-40 range."""


class TooManyHomeDrops(ValueError):
    """Raised when an order has more than three home drops."""


class NothingMeasured(ValueError):
    """Raised when a survey records neither rain nor wind."""


class PartialSurvey(ValueError):
    """Raised when exactly two of the three survey measures are present."""


class MissingReadings(ValueError):
    """Raised when more than one reading is missing."""


@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class HomeDrop:
    address: str
    kind: Literal["home"] = "home"


@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class LockerDrop:
    locker: str
    slot: int
    kind: Literal["locker"] = "locker"

    @model_validator(mode="after")
    def check_slot(self) -> "LockerDrop":
        if self.slot not in LOCKER_SLOTS:
            raise LockerSlotOutOfRange(self.slot)
        return self


@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class PickupDrop:
    point: str
    kind: Literal["pickup"] = "pickup"


def tag_legacy(data: object) -> object:
    if isinstance(data, dict) and "kind" not in data:
        return {"kind": next(k for k in ("address", "locker", "point") if k in data), **data}
    return data


@dataclass(frozen=True)
class Order:
    drops: list[Annotated[HomeDrop | LockerDrop | PickupDrop, BeforeValidator(tag_legacy), Field(discriminator="kind")]]
    note: str | None = None

    @model_validator(mode="after")
    def limit_home_drops(self) -> "Order":
        if len([d for d in self.drops if d.kind == "home"]) > MAX_HOME_DROPS:
            raise TooManyHomeDrops(len(self.drops))
        return self


@dataclass(frozen=True)
class Survey:
    rain_mm: float | None = None
    wind_kmh: float | None = None
    snow_cm: float | None = None
    readings: tuple[float | None, ...] = ()

    @model_validator(mode="after")
    def check_coverage(self) -> "Survey":
        if sum(v is not None for v in (self.rain_mm, self.wind_kmh)) == 0:
            raise NothingMeasured(self)
        if sum(v is not None for v in (self.rain_mm, self.wind_kmh, self.snow_cm)) == 2:
            raise PartialSurvey(self)
        if sum(1 for r in self.readings if r is None) > 1:
            raise MissingReadings(self.readings)
        return self
