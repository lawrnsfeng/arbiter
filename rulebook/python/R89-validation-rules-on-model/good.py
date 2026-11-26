from typing import Annotated, ClassVar, Literal, Self

from pydantic import BaseModel, BeforeValidator, Field, ValidationError, field_validator
from pydantic_core import ErrorDetails


class LabelRejected(ValueError):
    """General refusal: a limit the model enforces itself."""

    @classmethod
    def from_pydantic(cls, error: ValidationError) -> "LabelRejected":
        """The typed error a validator raised, else the general refusal."""
        first: ErrorDetails = error.errors()[0]
        match first:
            case {"type": "value_error", "ctx": {"error": LabelRejected() as typed}}:
                return typed
            case _:
                return cls(first["msg"])


class PostcodeError(LabelRejected):
    """A postcode with characters other than letters, digits and spaces."""


class LineCharsetError(LabelRejected):
    """A label line the printer cannot render (non-ASCII)."""


class Postcode(str):
    """A postcode, compacted and upper-cased.

    >>> Postcode("ab1 2cd")
    'AB12CD'
    >>> Postcode("ab-12")  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    PostcodeError: ab-12
    """

    def __new__(cls, value: str) -> Self:
        compact: str = value.replace(" ", "")
        if not compact.isalnum():
            raise PostcodeError(value)
        return super().__new__(cls, compact.upper())


class Label(BaseModel):
    # limits copied from the carrier's published label schema
    PRINTER_LINES: ClassVar[int] = 4
    MAX_WEIGHT_G: ClassVar[int] = 30_000

    lines: list[str] = Field(min_length=1, max_length=PRINTER_LINES)
    postcode: Annotated[str, BeforeValidator(Postcode)]
    services: frozenset[Literal["signature", "insured", "express"]] = frozenset()
    weight_g: int = Field(gt=0, le=MAX_WEIGHT_G)
    country: Literal["NO", "SE", "DK"]

    @field_validator("lines")
    @classmethod
    def check_printable(cls, lines: list[str]) -> list[str]:
        if not all(line.isascii() for line in lines):
            raise LineCharsetError(lines)
        return lines


def ship(carrier, raw: dict) -> str:
    try:
        label: Label = Label.model_validate(raw)
    except ValidationError as error:
        raise LabelRejected.from_pydantic(error) from error
    return carrier.book(label.model_dump(mode="json"))
