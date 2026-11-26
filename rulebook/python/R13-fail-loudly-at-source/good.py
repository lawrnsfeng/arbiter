import jsonschema


class ParcelError(Exception):
    """Base error of the parcel desk."""


class HandOverRefusedError(ParcelError):
    def __init__(self, reason: str) -> None:
        super().__init__(f"hand-over refused: {reason}")


class MissingAddressError(ParcelError):
    def __init__(self, code: str) -> None:
        super().__init__(f"parcel {code!r} has no address")


class Courier:
    def hand_over(self, parcel):
        receipt = self.desk.submit(parcel)
        if receipt.refused:
            raise HandOverRefusedError(receipt.reason)
        return receipt

    def try_hand_over(self, parcel) -> bool:
        """Tolerant probe: reports refusal instead of raising."""
        return not self.desk.submit(parcel).refused


def require_address(parcel):
    if not parcel.address:
        raise MissingAddressError(parcel.code)


def deliver(courier, parcel):
    require_address(parcel)
    return courier.hand_over(parcel)


def ship(courier, parcel):
    label = courier.label_for(parcel)
    require_address(parcel)
    return label


def import_manifest(raw, schema):
    manifest = raw.json()
    jsonschema.validate(manifest, schema)
    return manifest
