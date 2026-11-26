"""Weather report patterns."""

import re

STATION_CODE = re.compile(r"^[A-Z]{4}\d{2}$")  # expect: R50

TEMPERATURE = re.compile(r"(-?\d+)\s*C", re.IGNORECASE)  # expect: R50

RAINFALL = re.compile(r"(\d+(?:\.\d+)?)\s*mm", re.VERBOSE)  # expect: R50

WIND_LINE = re.compile(
    r"""
    ^Wind:\ +             # the label and its separator
    (\d+)                 # the speed in km/h
    \ blowing from\ (\w+)  # expect: R50
    """,
    re.VERBOSE,
)

# Pressure: 1013 hPa
PRESSURE = re.compile(  # expect: R50
    r"""
    ^Pressure:\ +         # the label
    (\d{3,4})
    \ hPa$                # the unit
    """,
    re.X,
)

# matches e.g. "Humidity: 81 %"
HUMIDITY = re.compile(  # expect-llm: R50
    r"""
    ^Humidity:\ +         # the label
    (\d{1,3})             # the relative humidity
    \ %$                  # the percent sign
    """,
    re.VERBOSE,
)

READING_TEXT: str = r"^\d+$"
READING = re.compile(READING_TEXT)  # expect: R50
