from enum import Enum
from typing import Final


class Stage(Enum):
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"


def describe(stage: Stage) -> str:
    match stage:
        case Stage.PACKED:
            return "waiting for pickup"
        case Stage.SHIPPED:
            return "on its way"
        case Stage.DELIVERED:
            return "arrived"


def is_done(stage: Stage) -> bool:
    if stage is Stage.DELIVERED:  # a single test is not a ladder
        return True
    return False


def compare(old: Stage, new: Stage) -> str:
    if old is Stage.PACKED:  # different subjects
        return "first scan"
    elif new is Stage.DELIVERED:
        return "final scan"
    return "in transit"


class Fallback:
    PRIMARY: Final[object] = object()
    SECONDARY: Final[object] = object()


def source_name(source: object) -> str:
    if source is Fallback.PRIMARY:  # sentinels of a plain class: not a closed set the detector can prove
        return "primary"
    elif source is Fallback.SECONDARY:
        return "secondary"
    return "none"


class Tracker:
    def pick(self, parcel) -> str:
        if parcel is self.pending:  # instance attributes, not members of a closed set
            return "pending"
        elif parcel is self.current:
            return "current"
        return "other"
