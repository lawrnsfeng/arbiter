import re


class Depot:
    def dispatch(self, parcels, van) -> float:
        # first, weigh everything  # expect: R75
        weights = [p.grams for p in parcels]
        # TODO(depot): split loads above the van limit  # expect: R75
        load = sum(weights)
        stock = self.stock
        stock -= len(parcels)  # subtract the dispatched parcels from stock  # expect-llm: R75
        # ===== van =====  # expect: R75
        van.fill(parcels)  # noqa: B018 temporary until the van API settles  # expect: R75
        unit = van.unit or "kg"  # unit is missing on older vans  # expect-llm: R75
        # kludge: the scale reports every parcel twice  # expect: R75
        # rv: why are the grams halved?  # expect-llm: R75
        return load / 2 if unit == "kg" else load


def route(depot_code: str, distance_km: float) -> list[str]:
    """Plan a delivery route.

    :param depot_code: depot code  # expect: R75
    :param distance_km: road distance in kilometres
    """
    return [depot_code] * int(distance_km)


# e.g. "PX-1042"  # expect-llm: R75
PARCEL_ID = re.compile(r"[A-Z]{2}-\d{4}")
