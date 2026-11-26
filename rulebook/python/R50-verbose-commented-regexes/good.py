"""Weather report patterns; each name says what it matches, each example lives here.

`STATION_CODE` — `OSLB07`
`WIND_LINE` — `Wind: 24 from NW`
`SEPARATED` — `12, 14; 9`
`CONDITION` — `cloudy`
`DEW_POINT` — `Dew point: 7`
`INLINE` — `42`
"""

import re
from re import VERBOSE

STATION_CODE = re.compile(
    r"""
    ^[A-Z]{4}             # the four-letter site prefix
    \d{2}$                # the two-digit sensor number
    """,
    re.VERBOSE,
)

WIND_LINE = re.compile(
    r"""
    ^Wind:\ +             # the label and its separator
    (\d+)                 # the speed in km/h
    \ from\ (\w+)         # the compass point it blows from
    """,
    re.VERBOSE | re.IGNORECASE,
)

SEPARATED = re.compile(
    r"""
    (\d+)                 # one reading
    [ ,;]*                # separators: a space inside a class is literal
    """,
    flags=re.X,
)

CONDITION = re.compile(
    r"""
    (?: clear | cloudy )  # the sky, spaces around the alternation are layout
    """,
    VERBOSE,
)

DEW_POINT_TEXT: str = r"""(?x)
    ^Dew\ point:\ +       # the label, verbose mode switched on inline
    (-?\d+)               # the dew point in degrees
    """
DEW_POINT = re.compile(DEW_POINT_TEXT)  # a pattern held in a variable that opens with `(?x)`

INLINE = re.compile(r"(?x)\d+  # the digits of one reading")

words: list[str] = "light rain".split(" ")  # not a regex
