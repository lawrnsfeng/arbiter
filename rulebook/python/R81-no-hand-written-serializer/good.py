from collections import Counter
from datetime import UTC, datetime
from typing import ClassVar, Self

from pydantic import BaseModel, Field, TypeAdapter, computed_field, field_serializer
from pydantic.dataclasses import dataclass


class Address(BaseModel):
    street: str
    city: str
    postcode: str


class Parcel(BaseModel):
    HEAVY_FROM_G: ClassVar[int] = 20_000

    code: str = Field(serialization_alias="tracking_code")
    weight_g: int
    status: str
    destination: Address
    internal_note: str = Field(default="", exclude=True)
    scans: list[str] = []

    @computed_field
    @property
    def heavy(self) -> bool:
        return self.weight_g > self.HEAVY_FROM_G

    @field_serializer("scans")
    def serialize_scans(self, scans: list[str]) -> list[str]:
        return sorted(scans)

    def as_carrier_v2_body(self) -> dict:
        return {"version": 2, "shipment": self.model_dump(mode="json", by_alias=True), "sent_at": datetime.now(UTC).isoformat()}

    def count_scans_per_depot(self) -> dict[str, int]:
        return dict(Counter(scan.split(":", 1)[0] for scan in self.scans))


def persist(parcel: Parcel) -> dict:
    return parcel.model_dump(mode="json", by_alias=True)


@dataclass(frozen=True)
class DepotCode:
    """Data-only and never dumped: a pydantic dataclass, validated at the boundary."""

    value: str = Field(pattern=r"^[A-Z]{3}\d$")

    @classmethod
    def from_scan(cls, raw: dict) -> Self:
        return DEPOT_CODE_ADAPTER.validate_python(raw)


DEPOT_CODE_ADAPTER: TypeAdapter[DepotCode] = TypeAdapter(DepotCode)
