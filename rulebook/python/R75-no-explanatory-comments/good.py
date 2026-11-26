#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from depot.loads import Load
from depot.patterns import PARCEL_ID


class OverweightLoadError(ValueError):
    """Raised when a van's load passes its limit; the caller splits the load across vans."""


class NotAParcelId(ValueError):
    """Raised for text that is not a depot code, a dash and a four-digit serial."""


class ParcelId(str):
    """A parcel id: two-letter depot, dash, four-digit serial, matched by `PARCEL_ID`.

    >>> ParcelId("PX-1042")
    'PX-1042'
    >>> ParcelId("PX1042")
    Traceback (most recent call last):
    NotAParcelId: PX1042
    """

    def __init__(self, text: str) -> None:
        if not PARCEL_ID.fullmatch(text):
            raise NotAParcelId(text)


class Depot:
    def dispatch(self, parcels, van) -> float:
        load: Load = van.load_of(parcels)
        if load.grams > van.limit_grams:
            raise OverweightLoadError(van.code)
        self.inventory.release(parcels)
        van.fill(parcels)  # type: ignore[arg-type]
        return load.kilograms

    def van_unit(self, van) -> str:
        if van.unit is None:  # pragma: no cover
            return van.default_unit()
        return van.unit


def route(depot_code: str, distance_km: float) -> list[str]:
    """Plan a delivery route.

    :param depot_code: two upper-case letters, e.g. "PX"
    :param distance_km: road distance in kilometres
    """
    return [depot_code] * int(distance_km)


TRACKING_URL = "https://example.org/track/a/very/long/path/that/keeps/going/until/it/crosses/the/line/limit/for/sure"  # noqa: E501

# fmt: off
ZONES = [
    1, 2,
    3, 4,
]
# fmt: on


def matching(ids: list[str]) -> list[str]:
    return [i for i in ids if PARCEL_ID.fullmatch(i)]  # shortcut: linear scan, index ids past 10k
