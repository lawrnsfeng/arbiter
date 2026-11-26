from typing import Annotated

import pydantic  # expect-llm: R26
from pydantic import AfterValidator, BaseModel, ConfigDict, TypeAdapter, field_validator


class Parcel(BaseModel):  # expect: R26
    tracking_id: str
    weight_g: int


@pydantic.dataclasses.dataclass
class Scan:  # expect: R26
    depot: str
    at: str


def parse_scan(raw: dict) -> Scan:
    return TypeAdapter(Scan).validate_python(raw)  # expect: R26


def parse_label(raw: dict) -> tuple[str, int]:
    if not isinstance(raw["tracking_id"], str):  # expect: R26
        raise TypeError("tracking_id")
    weight = raw.get("weight_g")
    if not isinstance(weight, int):
        raise TypeError("weight_g")
    return raw["tracking_id"], weight


def courier_name(raw: dict) -> str:
    return raw["courier"]["name"]  # expect: R26


@pydantic.dataclasses.dataclass(frozen=True, config=ConfigDict(extra="allow"))  # expect-llm: R26
class Window:
    opens: str
    note: str = ""  # expect-llm: R26

    @field_validator("opens", mode="before")
    @classmethod
    def _hhmm(cls, value: str) -> str:
        if ":" not in value:
            raise ValueError(f"not a time: {value!r}")  # expect: R26
        return value


def _postcode(value: str) -> str:
    if not value.strip():
        raise ValueError("blank postcode")  # expect: R26
    return value


Postcode = Annotated[str, AfterValidator(_postcode)]
