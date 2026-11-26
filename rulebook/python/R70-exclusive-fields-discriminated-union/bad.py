from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Delivery(BaseModel):
    address: str | None = None
    locker: str | None = None
    pickup_point: str | None = None

    @model_validator(mode="after")
    def one_target(self) -> "Delivery":
        chosen = sum(v is not None for v in (self.address, self.locker, self.pickup_point))  # expect: R70
        if chosen != 1:
            raise ValueError("choose exactly one delivery target")
        return self


@dataclass(frozen=True)
class Contact:
    email: str | None = None
    phone: str | None = None
    post: str | None = None

    def __post_init__(self) -> None:
        if [self.email, self.phone, self.post].count(None) != 2:  # expect: R70
            raise ValueError("exactly one contact channel")


class HomeDrop(BaseModel):  # expect: R70
    kind: Literal["home"] = "home"
    address: str


class LockerDrop(BaseModel):  # expect: R70
    model_config = ConfigDict(extra="forbid")
    locker: str
    slot: int


class PickupDrop(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["pickup"] = "pickup"
    point: str

    @model_validator(mode="before")  # expect: R70
    @classmethod
    def legacy(cls, data: dict) -> dict:
        return {"kind": "pickup", **data}


Drop = Annotated[HomeDrop | LockerDrop | PickupDrop, Field(discriminator="kind")]


class Order(BaseModel):
    drop: Drop
    fallback: HomeDrop | PickupDrop | None = None  # expect-llm: R70

    @model_validator(mode="after")
    def locker_slot(self) -> "Order":  # expect-llm: R70
        if isinstance(self.drop, LockerDrop) and not 1 <= self.drop.slot <= 40:
            raise ValueError("locker slot out of range")
        return self
