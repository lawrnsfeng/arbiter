from typing import Protocol


# <pkg>/typedefs.py
class Sensor(Protocol):
    @property
    def station(self) -> str: ...

    def last_reading(self) -> float | None: ...


class RainGauge:
    station: str

    def last_reading(self) -> float | None: ...

    def tip_count(self) -> int: ...


class Anemometer:
    station: str

    def last_reading(self) -> float | None: ...

    def gust(self) -> float: ...


def describe(sensor: Sensor) -> str:
    return f"{sensor.station}: {sensor.last_reading()}"


# look-alike: the function tells the members apart
def headline(sensor: RainGauge | Anemometer) -> str:
    if isinstance(sensor, RainGauge):
        return f"{sensor.tip_count()} tips"
    return f"gust {sensor.gust()}"


# look-alike: optional scalar
def rounded(value: float | None, places: int | None = None) -> str: ...


# look-alike: union with a class this codebase does not define
def archive(target: RainGauge | Path) -> None: ...
