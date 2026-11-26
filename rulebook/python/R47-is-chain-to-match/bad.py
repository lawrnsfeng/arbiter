from enum import Enum, StrEnum

import parcels


class Stage(Enum):
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"


class Lane(StrEnum):
    EXPRESS = "express"
    ECONOMY = "economy"


def lane_cost(parcel) -> float:
    if parcel.lane is Lane.EXPRESS:  # expect: R47
        return 12.0
    if parcel.lane is Lane.ECONOMY:
        return 4.0
    return 0.0


def describe(stage: Stage) -> str:
    if stage is Stage.PACKED:  # expect: R47
        return "waiting for pickup"
    elif stage is Stage.SHIPPED:
        return "on its way"
    else:
        return "arrived"


def notify(parcel, outbox) -> None:
    if parcel.stage is Stage.SHIPPED:  # expect: R47
        outbox.send(parcel.owner, "shipped")
    if parcel.stage is Stage.DELIVERED:
        outbox.send(parcel.owner, "delivered")


def fee(parcel) -> float:
    cost: float = 0.0
    for item in parcel.items:
        if item.kind is parcels.Size.SMALL:  # expect-llm: R47
            cost += 2.0
        elif item.kind is parcels.Size.MEDIUM:
            cost += 4.5
        elif item.kind is parcels.Size.LARGE:
            cost += 9.0
    return cost


def badge(stage: Stage | None) -> str:
    if stage is None:
        return ""
    if stage is Stage.PACKED:  # expect: R47
        return "box"
    if stage is Stage.SHIPPED:
        return "truck"
    return "house"
