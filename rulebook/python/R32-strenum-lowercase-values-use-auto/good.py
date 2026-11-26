from enum import Enum, StrEnum, auto


class Sky(StrEnum):
    CLEAR = auto()
    OVERCAST = auto()
    FEELS_LIKE = "feels-like"
    PRESSURE = "hPa"


# look-alike: a str mixin Enum, where auto() would not yield the name
class Station(str, Enum):
    NORTH = "north"


# look-alike: a plain namespace of strings
class Columns:
    TEMPERATURE = "temperature"
