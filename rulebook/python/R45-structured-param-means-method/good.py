from dataclasses import dataclass


@dataclass
class ParcelRoute:
    stops: list[str]
    distance_km: float
    speed_kmh: float

    def eta(self, traffic: float) -> float:
        return self.distance_km / (self.speed_kmh * traffic)

    def has_stop(self, stop: str) -> bool:
        return self._normalise(stop) in {self._normalise(s) for s in self.stops}

    @staticmethod
    def _normalise(stop: str) -> str:
        """Compare stops case- and whitespace-insensitively."""
        return stop.strip().lower()


class Courier:
    name: str


class Locker:
    capacity: int
    occupied: set[str]

    @property
    def free_slots(self) -> int:
        return self.capacity - len(self.occupied)


def prompt_compaction(locker: Locker) -> None:
    if input(f"{locker.free_slots} free slots; compact? ") == "y":
        locker.occupied.clear()


# look-alike: crosses two classes
def route_assign(route: ParcelRoute, courier: Courier) -> str:
    return f"{courier.name} takes {route.stops[0]}"


# look-alike: the structured parameter is not first
def route_label(prefix: str, route: ParcelRoute) -> str:
    return f"{prefix}{route.stops[0]}"


# look-alike: a registered callback must stay a free function
@app.on_event("dispatch")
def route_dispatched(route: ParcelRoute) -> None:
    print(route.stops)
