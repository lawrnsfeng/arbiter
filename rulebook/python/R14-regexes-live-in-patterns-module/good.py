"""Library-catalogue patterns; each name says what it matches, each example lives here.

`SHELF_CODE` — `SHELF 12-B`
`ISBN_LINE` — `ISBN 978-0441013593`
`DUE_DATE` — `due 2026-03-14`
`LOAN_STATE` — `overdue` (compiled with `re.VERBOSE` imported under another name)
`RENEWAL` — `renewed 2 times` (verbose mode switched on inline)
"""

import re
from re import VERBOSE as LAYOUT

SHELF_CODE = re.compile(
    r"""
    SHELF\ (\d+)   # the shelf number
    -([A-Z])       # the bay letter
    """,
    re.VERBOSE,
)

ISBN_LINE = re.compile(
    r"""
    ISBN\ (\d{3}-\d{10})   # the 13-digit ISBN after its label
    """,
    re.VERBOSE,
)

DUE_DATE = re.compile(
    r"""
    due \s (\d{4}-\d{2}-\d{2})   # ISO date after the word due
    """,
    re.VERBOSE,
)

LOAN_STATE = re.compile(
    r"""
    (?: on\ loan | overdue )   # the two states a lent copy can be in
    """,
    LAYOUT,
)

RENEWAL = re.compile(
    r"""(?x)                    # verbose mode, switched on inline
    renewed \s (\d+) \s times   # the renewal count on a loan slip
    """
)

SHELF_PREFIX = re.escape("SHELF ")
CARD_FORMAT = r"CARD-(\d{6})"
