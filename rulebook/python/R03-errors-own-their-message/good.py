from string import Template
from typing import ClassVar

from fastapi import HTTPException


class ParcelError(Exception):
    """Base error: renders the subclass's template once; `raw` passes pre-rendered text through untouched."""

    TEMPLATE: ClassVar[Template] = Template("parcel tracker error")

    def __init__(self, *, raw: str | None = None, **values: str) -> None:
        super().__init__(raw if raw is not None else type(self).TEMPLATE.substitute(**values))


class ParcelNotFoundError(ParcelError):
    TEMPLATE = Template("no parcel with code $code")

    def __init__(self, code: str) -> None:
        super().__init__(code=repr(code))


class RouteClosedError(ParcelError):
    TEMPLATE = Template("the route is closed")


class HubUnreachableError(ParcelError):
    TEMPLATE = Template("hub $hub unreachable")

    def __init__(self, hub: str) -> None:
        super().__init__(hub=hub)


class ShippingError(Exception):
    """Base error of the shipping desk."""


class UnreadableLabelError(ShippingError):
    def __init__(self, label: str) -> None:
        super().__init__(f"unreadable label {label!r}")


class CourierBusyError(ShippingError):
    def __init__(self, courier: str, *, retryable: bool = False) -> None:
        super().__init__(f"courier {courier} is busy")
        self.retryable = retryable


class Archived(HTTPException):
    """410 for anything the archive swallowed; callers name only what is gone."""

    STATUS = 410

    def __init__(self, what: str) -> None:
        super().__init__(self.STATUS, {"error": {"code": "archived", "message": f"{what} was archived"}})


def track_many(codes, archive):
    gone = next((c for c in codes if c in archive), None)
    if gone is not None:
        raise Archived(gone)
    return [archive.lookup(c) for c in codes]


async def delete_label(code, labels):
    if code not in labels:
        raise Archived(f"label {code}")
    return labels.pop(code)


def conflict_route(parcel_id, store):
    if store[parcel_id].locked:
        raise HTTPException(status_code=409, detail="Parcel locked")
    return store[parcel_id]


def describe(parcel):
    text = f"parcel {parcel.code}"
    print(text)
    return text


def deliver(parcel, courier):
    try:
        courier.hand_over(parcel)
    except ParcelError as err:
        raise err
