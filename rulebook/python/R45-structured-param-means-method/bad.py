from dataclasses import dataclass


@dataclass
class ParcelRoute:
    stops: list[str]
    distance_km: float
    speed_kmh: float


class Locker:
    capacity: int
    occupied: set[str]


def route_eta(route: ParcelRoute, traffic: float) -> float:  # expect: R45
    return route.distance_km / (route.speed_kmh * traffic)


def _parcel_route_has_stop(route: ParcelRoute, stop: str) -> bool:  # expect: R45
    return _normalise(stop) in {_normalise(s) for s in route.stops}


def _normalise(stop: str) -> str:  # expect-llm: R45
    """Called only from the function above: moves with it as a staticmethod."""
    return stop.strip().lower()


def locker_report(locker: "Locker", *, verbose: bool = False) -> dict:  # expect: R45
    free = locker.capacity - len(locker.occupied)
    return {"free": free, "used": sorted(locker.occupied)} if verbose else {"free": free}


def prompt_free_space(locker: Locker) -> None:  # expect-llm: R45
    """No name tell, but it computes from the locker's fields before asking."""
    free = locker.capacity - len(locker.occupied)
    if input(f"{free} free slots; compact? ") == "y":
        locker.occupied.clear()
