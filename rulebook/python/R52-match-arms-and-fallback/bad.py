from enum import Enum
from typing import Literal

type Speed = Literal["standard", "express"]


class Carrier(Enum):
    POST = "post"
    COURIER = "courier"
    LOCKER = "locker"


def is_tracked(carrier: Carrier) -> bool:
    match carrier:  # expect: R52
        case Carrier.COURIER:
            return True


def size_label(size: str) -> str:
    match size:  # expect: R52
        case "S":
            return "small"
        case "M" | "L":
            return "regular"


def kind_of(value: object) -> str:
    match value:  # expect: R52
        case int() | float():
            return "number"
        case str():
            return "text"


def shipping_days(carrier: Carrier) -> int:
    match carrier:
        case Carrier.POST:
            return 3
        case Carrier.COURIER | Carrier.LOCKER:
            return 1
        case _:  # expect: R52
            return 2


def handling(carrier: Carrier) -> str:
    match carrier:
        case Carrier.POST | Carrier.LOCKER:
            return "drop at counter"
        case Carrier.COURIER:
            print("courier collects")  # expect-llm: R52


def label_colour(speed: Speed) -> str:
    match speed:
        case "standard":
            return "white"
        case "express":
            return "orange"
        case _:  # expect: R52
            return "grey"


def strap(size: Literal["S", "M", "L"]) -> str:
    match size:  # expect: R52
        case "S":
            return "green"
        case "M":
            return "amber"
