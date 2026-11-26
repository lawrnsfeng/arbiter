from collections import UserString
from datetime import datetime, time
from enum import Enum

from weatherkit.constants import ABSOLUTE_ZERO_C


class IsbnText(str):
    """An ISBN with the hyphens removed.

    >>> IsbnText("978-0-13-468599-1")
    '9780134685991'
    """

    def __new__(cls, raw: str) -> "IsbnText":
        return super().__new__(cls, raw.replace("-", ""))


class BelowAbsoluteZero(ValueError):
    """Raised for a reading colder than absolute zero."""


class Celsius(int):
    """A whole-degree temperature reading.

    >>> Celsius(21)
    21
    >>> Celsius(-300)
    Traceback (most recent call last):
    BelowAbsoluteZero: -300
    """

    def __new__(cls, value: int) -> "Celsius":
        if value < ABSOLUTE_ZERO_C:
            raise BelowAbsoluteZero(value)
        return super().__new__(cls, value)


class Unit(str, Enum):
    CELSIUS = "C"
    FAHRENHEIT = "F"


class Caption(UserString):
    """A recipe caption."""


class Station:
    """A weather station identified by its code."""

    def stamp_opening(self) -> str:
        """Today's opening stamp.

        >>> datetime.now().strftime("%H:%M")  # doctest: +SKIP
        '06:00'
        """
        return datetime.now().strftime("%H:%M")

    def slot(self, start: time) -> str:
        """Label a fixed observation slot.

        >>> Station().slot(time(6, 0))
        'slot-0600'
        """
        return f"slot-{start:%H%M}"
