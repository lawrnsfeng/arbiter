from datetime import datetime


class IsbnText(str):  # expect: R64
    """An ISBN with the hyphens removed."""

    def __new__(cls, raw: str) -> "IsbnText":
        return super().__new__(cls, raw.replace("-", ""))


class Grams(int):  # expect: R64
    def as_kilograms(self) -> float:
        return self / 1000


class ShelfTag(bytes):  # expect: R64
    """Two ASCII letters followed by a big-endian 16-bit shelf number."""


class Celsius(int):
    """A whole-degree temperature reading.

    >>> Celsius(21)
    21
    """

    def __new__(cls, value: int) -> "Celsius":  # expect: R64
        if value < -273:
            raise ValueError(f"below absolute zero: {value}")
        return super().__new__(cls, value)


class Reading:
    def stamped(self) -> str:
        """Prefix the reading with the current time.

        >>> Reading().stamped()  # expect-llm: R64
        '2026-01-01T00:00 21C'
        >>> datetime.now().year > 2000  # expect: R64
        True
        """
        return f"{datetime.now():%Y-%m-%dT%H:%M} {self}"


def parse_reading(text: str) -> float:  # expect-llm: R64
    """Read a sensor line such as station id, colon, tenths of a degree."""
    _, _, tenths = text.partition(":")
    return int(tenths) / 10
