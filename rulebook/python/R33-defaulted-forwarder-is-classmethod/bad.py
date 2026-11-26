import settings

METRIC = "metric"


class Shipment:
    def __init__(self, origin: str, weight_kg: float, *, fragile: bool = False) -> None: ...

    @classmethod
    def from_origin(cls, origin: str, weight_kg: float, *, fragile: bool = False) -> "Shipment": ...


class ScaleReading:
    def __init__(self, units: str, grams: int, scale_id: str) -> None: ...


def _hub_shipment(weight_kg: float, *, fragile: bool = False) -> Shipment:  # expect: R33
    """Every caller ships from the configured hub."""
    return Shipment.from_origin(settings.home_depot, weight_kg, fragile=fragile)


def _metric_reading(grams: int, scale_id: str) -> ScaleReading:  # expect: R33
    return ScaleReading(METRIC, grams, scale_id)


async def _express(weight_kg: float) -> Shipment:  # expect: R33
    return Shipment(settings.express_counter.code, weight_kg)
