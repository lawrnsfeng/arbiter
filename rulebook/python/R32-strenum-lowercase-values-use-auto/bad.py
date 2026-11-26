import enum
from enum import StrEnum, auto


class Sky(StrEnum):
    CLEAR = "clear"  # expect: R32
    OVERCAST = "overcast"  # expect: R32
    LIGHT_RAIN = auto()


class ReadingField(enum.StrEnum):
    WIND_SPEED = "wind_speed"  # expect: R32
    PRESSURE = "hPa"


class Season(StrEnum):
    winter = "winter"  # expect: R32
    SPRING = "Spring"
