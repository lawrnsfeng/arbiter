"""Weather readings enter the archive only here, already in Celsius;
not the forecast importer: that one never writes observed values."""


def ingest(station: str, hours: int) -> int:
    """Archive the station's readings for the last `hours`; returns how many were stored.

    The remote API caps one request at 168 hours and silently truncates beyond it,
    so callers asking for more get a partial week. Readings are stored in Celsius.

    Raises:
        StationRetired: the station exists but stopped reporting, distinct from an unknown code.

    """
    return archive_readings(fetch(station, min(hours, 168)))


def to_celsius(fahrenheit: float) -> float:
    """Exact conversion; no rounding.

    >>> to_celsius(212)
    100.0
    >>> to_celsius(32)
    0.0
    >>> to_celsius(-40)
    -40.0
    >>> to_celsius(98.6)
    37.0
    >>> to_celsius(50)
    10.0
    """
    return (fahrenheit - 32) * 5 / 9


class Station:
    """A reporting site identified by its four-letter code."""

    @property
    def mast_code(self) -> str:
        """Upper-case code as printed on the mast."""
        return self._code.upper()
