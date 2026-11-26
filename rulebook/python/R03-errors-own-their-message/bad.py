from fastapi import HTTPException


class ParcelError(Exception):
    """Base error of the parcel tracker."""


def find_parcel(store, code):
    parcel = store.get(code)
    if parcel is None:
        missing = f"no parcel with code {code!r}"
        raise LookupError(missing)  # expect: R3
    return parcel


def check_weight(grams):
    if grams <= 0:
        note = "weight must be positive, got " + str(grams)
        raise ParcelError(note) from None  # expect: R3


class LabelError(ParcelError):
    def __init__(self, label):
        text = f"unreadable label {label!r}"
        super().__init__(text)  # expect: R3


class RouteError(ParcelError):
    def __init__(self, hub=None, closed=False):  # expect: R3
        if closed:
            super().__init__("the route is closed")  # expect: R3
        elif hub is None:
            super().__init__("no hub on the route")  # expect: R3
        else:
            super().__init__(f"hub {hub} unreachable")  # expect: R3


class CustomsError(ParcelError):
    TEMPLATE = "parcel {code} held at customs"

    def __init__(self, **values):
        super().__init__(self.TEMPLATE.format(**values))  # expect: R3


class DamagedError(ParcelError):
    def __init__(self, code):  # expect: R3
        """The parcel arrived damaged."""


class LostError(ParcelError):
    def __init__(self):
        super().__init__()  # expect: R3


def track_many(codes, archive):
    for code in codes:
        if code in archive:
            raise HTTPException(410, f"{code} was archived")  # expect: R3
    return [archive.lookup(c) for c in codes]


async def delete_label(code, labels):
    try:
        return labels.pop(code)
    except KeyError:
        raise HTTPException(  # expect: R3
            status_code=410, detail={"error": {"code": "label_archived", "message": code}}
        ) from None


def cancel(parcel):
    if parcel.shipped:
        raise RuntimeError("cannot cancel a shipped parcel")  # expect: R3


def open_depot(host):
    if not host:
        raise ConnectionError  # expect: R3
    return host


class QuotaError(ValueError):  # expect-llm: R3
    """A refusal deriving straight from a builtin although the project has `ParcelError`."""
