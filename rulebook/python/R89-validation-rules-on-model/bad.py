from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.dataclasses import dataclass as pydantic_dataclass

SUPPORTED_COUNTRIES = {"NO", "SE", "DK"}


class LabelPrinter:
    def print_label(self, label: dict) -> bytes:
        if len(label["lines"]) > 4:
            raise ValueError("label has %d lines, the printer takes 4" % len(label["lines"]))  # expect: R89
        return render(label)


def normalise_postcode(code: str) -> str:
    if code.replace(" ", "").isalnum():
        return code.upper()
    else:
        raise ValueError("unreadable postcode {}".format(code))  # expect: R89


def weight_grams(raw: str) -> int:
    try:
        return int(float(raw) * 1000)
    except (TypeError, ValueError) as exc:
        raise ValueError("weight must be numeric: " + str(raw)) from exc  # expect: R89


class Postcode(str): ...


class Label(BaseModel):
    lines: list[str]
    postcode: Postcode  # expect-llm: R89


def ship(carrier, label: Label, country: str) -> str:
    booking = carrier.book(label.model_dump())
    if country not in SUPPORTED_COUNTRIES:  # expect-llm: R89
        carrier.cancel(booking)
        raise ValueError(f"cannot ship to {country}")
    return booking


@pydantic_dataclass
class CustomsForm:  # expect-llm: R89
    items: list[str] = Field(max_length=20)
    value_cents: int = Field(gt=0)

    @field_validator("items")
    @classmethod
    def check_items(cls, items: list[str]) -> list[str]:
        return [i.strip() for i in items]

    @model_validator(mode="after")
    def check_declared_value(self) -> "CustomsForm":
        return self
