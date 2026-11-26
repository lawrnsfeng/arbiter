"""Constants of the lending desk, grouped by category."""

from datetime import timedelta
from enum import StrEnum, auto

ISBN_LENGTH = 13
CATALOGUE_REMOTE = "https://example.org/catalogue.git"
PAGE_SIZE = 50
PAGE_MAX = 500


class Loan:
    PERIOD: timedelta = timedelta(days=21)
    RENEWALS_MAX: int = 2


class Fine:
    PER_DAY: float = 0.25
    CAP: float = 10.0


class Collection(StrEnum):
    REFERENCE = auto()
    CIRCULATING = auto()
    ARCHIVED = auto()
