from dataclasses import dataclass

from pydantic import BaseModel, TypeAdapter
from pydantic.dataclasses import dataclass as pydantic_dataclass


@dataclass(frozen=True, slots=True)
class Address:
    street: str
    city: str
    postcode: str

    def as_dict(self) -> dict[str, str]:  # expect: R81
        return dict(street=self.street, city=self.city, postcode=self.postcode)


class Parcel(BaseModel):
    code: str
    weight_g: int
    status: str
    destination: Address

    def to_payload(self) -> dict:  # expect: R81
        return {"code": self.code, "weight": self.weight_g, "status": self.status, "destination": self.destination.as_dict()}

    def wire(self) -> dict:  # expect: R81
        body = {"tracking_code": self.code, "grams": self.weight_g}
        return body

    def as_body(self) -> dict:  # expect: R81
        return {**self.model_dump(), "status": self.status.upper()}

    def snapshot(self) -> dict:  # expect: R81
        data = self.model_dump()
        data["weight_g"] = round(self.weight_g, -1)
        return data

    def label(self) -> dict:  # expect: R81
        out = self.model_dump(mode="json")
        out.update(status=self.status.title())
        return out

    def manifest(self) -> dict:  # expect: R81
        row = self.model_dump()
        row |= {"scanned": sorted(row.get("scans", []))}
        return row

    def fields_out(self) -> dict:  # expect-llm: R81
        return {name: getattr(self, name) for name in ("code", "weight_g", "status")}


@pydantic_dataclass(frozen=True)
class Shipment:
    parcel_code: str
    depot: str


SHIPMENT_ADAPTER = TypeAdapter(Shipment)


def archive(shipment: Shipment) -> dict:
    return SHIPMENT_ADAPTER.dump_python(shipment, mode="json")  # expect: R81


def receipt(shipment: Shipment) -> bytes:
    return TypeAdapter(Shipment).dump_json(shipment)  # expect: R81


SHIPMENTS_ADAPTER = TypeAdapter(list[Shipment])


def manifest_rows(items: list[Shipment]) -> list[dict]:
    return SHIPMENTS_ADAPTER.dump_python(items, mode="json")  # expect: R81


def by_depot(index: dict[str, Shipment | None]) -> bytes:
    return TypeAdapter(dict[str, Shipment | None]).dump_json(index)  # expect: R81


class DepotCode(BaseModel):  # expect-llm: R81
    # holds one value, parsed once, never dumped: a pydantic dataclass is enough
    value: str
