from enum import StrEnum, auto


class Units(StrEnum):
    METRIC = auto()
    IMPERIAL = auto()


class Station:
    def __init__(self, code: str, units: Units = Units.METRIC) -> None:
        self._code = code
        self.units = units
        self._calibration: dict[str, float] = {}

    @property
    def code(self) -> str:
        return self._code

    def calibrate(self, sensor: str, delta: float) -> None:
        self._calibration[sensor] = delta

    def offset(self, sensor: str) -> float:
        return self._calibration.get(sensor, 0.0)

    def peak_gust(self, readings: list["Reading"]) -> float:
        return max(r.gust_kph + self.offset("anemometer") for r in readings)

    # Look-alikes: the prefix is not get_/set_.
    def reset_offsets(self) -> None:
        self._calibration = {}

    def budget_minutes(self) -> int:
        return 30

    def asset_tag(self, prefix: str) -> str:
        return f"{prefix}-{self._code}"


class StationList(ThirdPartyView):
    # Look-alike: a hook forced by a third-party base class.
    def get_queryset(self):
        return self.stations
