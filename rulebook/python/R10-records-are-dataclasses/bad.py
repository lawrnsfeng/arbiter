from collections.abc import Mapping
from typing import TypedDict

Reading = dict[str, float | str]  # expect: R10
type Forecast = Mapping[str, object]  # expect: R10


class StationInfo(TypedDict):  # expect: R10
    name: str
    altitude_m: int


Alert = TypedDict("Alert", {"level": str, "text": str})  # expect: R10


def latest(station, sensor):
    value = sensor.read()
    return {"station": station.name, "celsius": value, "taken_at": sensor.clock()}  # expect: R10


def extremes(readings):
    pair = (min(readings), max(readings))  # expect-llm: R10
    return pair
