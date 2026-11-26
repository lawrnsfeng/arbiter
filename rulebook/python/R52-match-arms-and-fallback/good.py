from enum import Enum
from typing import Literal

from parcels.errors import UnknownCarrier, UnknownSize


class Carrier(Enum):
    POST = "post"
    COURIER = "courier"
    LOCKER = "locker"


def is_tracked(carrier: Carrier) -> bool:
    if carrier is Carrier.COURIER:
        return True
    return False


def shipping_days(carrier: Carrier) -> int:
    match carrier:
        case Carrier.POST:
            return 3
        case Carrier.COURIER | Carrier.LOCKER:
            return 1


def size_label(size: str) -> str:
    match size:
        case "S":
            return "small"
        case "M" | "L":
            return "regular"
        case _:
            raise UnknownSize(size)


def corner(point: tuple[int, int]) -> str:
    match point:
        case (0, 0):
            return "origin"
        case (x, 0):
            return f"on the x axis at {x}"
        case _:
            return "elsewhere"


def strap_colour(size: Literal["S", "M", "L"]) -> str:
    match size:  # a Literal subject is a closed set: every value covered, no fallback
        case "S":
            return "green"
        case "M":
            return "amber"
        case "L":
            return "red"


def legacy_days(carrier) -> int:
    match carrier:  # an unannotated subject is open, whatever the patterns name: `case _` is required
        case Carrier.POST:
            return 3
        case Carrier.COURIER | Carrier.LOCKER:
            return 1
        case _:
            raise UnknownCarrier(carrier)
