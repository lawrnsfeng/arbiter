from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import NewType, Self

Celsius = NewType("Celsius", float)


class Depot: ...


class Courier: ...


class Lane(StrEnum):
    NORTH = "n"
    SOUTH = "s"


class ParcelId(str): ...


class LockerId(ParcelId): ...


@dataclass(frozen=True)
class Handover:
    depot: Depot
    courier: Courier

    @classmethod
    def from_parcel(cls, parcel_id: str) -> Self:
        depot = Depot.nearest(parcel_id)
        return cls(depot, Courier.on_shift(depot))


def dispatch(parcel_id: str) -> None:
    handover = Handover.from_parcel(parcel_id)
    handover.courier.collect(handover.depot)


# look-alikes: scalar tuples, value types, homogeneous tuples
def position(parcel) -> tuple[float, float]: ...


def weight_row(parcel) -> tuple[str, int]: ...


def label_files(parcel) -> tuple[Path, Path]: ...


def depots_on_route(parcel) -> tuple[Depot, ...]: ...


def temperature_range(parcel) -> tuple[Celsius, Celsius]: ...


def lanes(parcel) -> tuple[Lane, Lane]: ...


def ids(parcel) -> tuple[ParcelId, LockerId]: ...
