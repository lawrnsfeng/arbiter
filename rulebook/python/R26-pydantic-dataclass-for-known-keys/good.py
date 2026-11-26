import dataclasses
from dataclasses import field
from typing import Annotated, ClassVar

from pydantic import AfterValidator, BaseModel, Field, TypeAdapter, ValidationError, model_validator
from pydantic.dataclasses import dataclass


class ParcelError(Exception):
    def __init__(self, problems: int) -> None:
        super().__init__(f"parcel record rejected: {problems} problem(s)")

    @classmethod
    def from_pydantic(cls, err: ValidationError) -> "ParcelError":
        return cls(err.error_count())


class BlankPostcodeError(ValueError):
    def __init__(self) -> None:
        super().__init__("postcode is blank")


def _postcode(value: str) -> str:
    """Reject a blank postcode.

    Stays free: any record with a postcode field reuses this validator.
    """
    if not value.strip():
        raise BlankPostcodeError()
    return value


@dataclass(frozen=True)
class Parcel:
    OWNED: ClassVar[frozenset[str]] = frozenset({"tracking_id", "weight_g", "postcode", "note"})
    tracking_id: str
    weight_g: int
    postcode: Annotated[str, AfterValidator(_postcode)]
    note: str | None = None
    passthrough: dict[str, object] = field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _collect_passthrough(cls, raw: dict[str, object]) -> dict[str, object]:
        """Move keys the record does not own into `passthrough`."""
        owned: dict[str, object] = {k: v for k, v in raw.items() if k in cls.OWNED}
        return {**owned, "passthrough": {k: v for k, v in raw.items() if k not in cls.OWNED}}

    @classmethod
    def from_record(cls, raw: object) -> "Parcel":
        try:
            return _PARCEL.validate_python(raw)
        except ValidationError as err:
            raise ParcelError.from_pydantic(err) from err


_PARCEL = TypeAdapter(Parcel)


# Look-alikes.
class TrackingView(BaseModel):
    """Returned by a web route, which dumps it (a BaseModel need)."""

    tracking_id: str
    status: str


@router.get("/parcels/{tracking_id}", response_model=TrackingView)
def track(tracking_id: str):
    return parcel_status(tracking_id)


class Receipt(BaseModel):
    """Returned from a decorated route function, which dumps it."""

    tracking_id: str
    signed_by: str


@router.post("/parcels/{tracking_id}/receipt")
def sign(tracking_id: str, signer: str) -> Receipt:
    return Receipt(tracking_id=tracking_id, signed_by=signer)


class Address(BaseModel):
    """Never dumped, but its fields carry Field constraints (a BaseModel need)."""

    street: str = Field(min_length=1, max_length=120)
    postcode: str = Field(pattern=r"^[A-Z0-9 ]{3,10}$")

    @classmethod
    def from_record(cls, raw: object) -> "Address":
        return cls.model_validate(raw)


class UnreadableWeightError(ValueError):
    def __init__(self, raw: object) -> None:
        super().__init__(f"unreadable weight: {raw!r}")


@dataclasses.dataclass
class Tally:
    count: int


def weight_of(value: int | str) -> int:
    match value:
        case int():
            return value
        case str():
            return int(value.removesuffix("g"))
        case _:
            raise UnreadableWeightError(value)


def corner(grid: list[list[int]]) -> int:
    return grid[0][1]


# Look-alike: a ValueError subclass raised outside any validator.
def checked_count(text: str) -> int:
    if not text.isdigit():
        raise UnreadableWeightError(text)
    return int(text)
