from typing import Tuple


class Depot: ...


class Courier: ...


class Manifest: ...


class Invoice: ...


class Carrier: ...


def _route_for(parcel_id: str) -> tuple[Depot, Courier]:  # expect: R40
    depot = Depot.nearest(parcel_id)
    return depot, Courier.on_shift(depot)


def dispatch(parcel_id: str) -> None:
    depot, courier = _route_for(parcel_id)
    courier.collect(depot)


def load_shipment(code: str) -> Tuple[Manifest, carriers.Carrier, Invoice]:  # expect: R40
    ...


async def fetch_handover(parcel) -> tuple["Depot", "Courier"]:  # expect: R40
    ...


def split_route(parcel):  # expect-llm: R40
    depot = Depot.lookup(parcel.origin)
    courier = Courier.assigned(parcel)
    return depot, courier
