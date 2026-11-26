_MAX_GUST_KMH = 150  # expect: R36
STATION_PREFIXES: tuple[str, ...] = ("WX", "MET")  # expect: R36


class GustFilter:
    _SMOOTHING = 0.3  # expect: R36

    def keep(self, reading) -> bool:
        return reading.gust <= _MAX_GUST_KMH


class StationIndex:
    def accepts(self, code: str) -> bool:
        return code.startswith(STATION_PREFIXES)


class Dewpoint:
    _MAGNUS_B: float = 17.62  # expect: R36
