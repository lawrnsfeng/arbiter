"""Shipping helpers whose types already say what the checker needs, so nothing carries a `# noqa`."""

from dataclasses import dataclass


class MissingScheduleError(LookupError):
    def __init__(self, parcel_id: str) -> None:
        super().__init__(f"no delivery schedule for parcel {parcel_id}")


def eta_hours(parcel_id: str, schedule: dict[str, int] | None) -> int:
    """Hours until delivery; a missing schedule is an error, not an ignored type."""
    if schedule is None:
        raise MissingScheduleError(parcel_id)
    return schedule[parcel_id]


def to_kilograms(grams: int) -> float:
    """Convert grams to kilograms."""
    return grams / 1000


@dataclass(frozen=True)
class Shipment:
    origin: str
    destination: str
    weight_g: int
    priority: bool = False
    insured: bool = False


def dispatch(shipment: Shipment, courier: "Courier") -> str:
    """Book one shipment with a courier."""
    return courier.book(shipment)


# Look-alike: prose and strings that mention suppressions are not suppressions.
HINT = "never add `# type: ignore`; fix the type instead"
