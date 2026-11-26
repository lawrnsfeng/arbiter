from typing import Union


class RainGauge:
    station: str
    battery_level: float

    def last_reading(self) -> float | None: ...


class Anemometer:
    station: str
    battery_level: float

    def last_reading(self) -> float | None: ...


class Thermometer:
    def __init__(self, station: str) -> None:
        self.station = station
        self.battery_level = 1.0


def describe(sensor: RainGauge | Anemometer) -> str:  # expect: R42
    return f"{sensor.station}: {sensor.last_reading()}"


def silent_stations(by_station: dict[str, RainGauge | Anemometer]) -> set[str]:  # expect: R42
    silent = set()
    for gauge in by_station.values():
        if gauge.last_reading() is None:
            silent.add(gauge.station)
    return silent


def battery(sensor: Union[RainGauge, Anemometer, Thermometer]) -> float:  # expect: R42
    return sensor.battery_level


class Instrument:  # expect-llm: R42
    """A base added only so unrelated gauges can share one parameter type."""

    station: str


class Hygrometer(Instrument):
    pass


class Barometer(Instrument):
    pass
