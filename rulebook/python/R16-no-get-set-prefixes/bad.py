_UNITS = "metric"


def get_units() -> str:  # expect: R16
    return _UNITS


def set_units(system: str) -> None:  # expect: R16
    global _UNITS
    _UNITS = system


class Station:
    def __init__(self, code: str) -> None:
        self._code = code
        self._calibration: dict[str, float] = {}

    def get_code(self) -> str:  # expect: R16
        """The station's registry code."""
        return self._code

    def set_offset(self, sensor: str, delta: float) -> None:  # expect: R16
        self._calibration[sensor] = delta

    def get_offset(self, sensor: str) -> float:  # expect: R16
        return self._calibration.get(sensor, 0.0)

    def get_peak_gust(self, readings: list["Reading"]) -> float:  # expect-llm: R16
        return max(r.gust_kph + self._calibration.get("anemometer", 0.0) for r in readings)
