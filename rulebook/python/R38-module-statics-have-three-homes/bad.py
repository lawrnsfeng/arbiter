"""Constants of the lending desk."""

from datetime import timedelta

LOAN_PERIOD: timedelta = timedelta(days=21)  # expect: R38
LOAN_RENEWALS_MAX: int = 2  # expect: R38
LOAN_GRACE_DAYS = 3  # expect: R38
FINE_PER_DAY = 0.25  # expect: R38
FINE_CAP = 10.0  # expect: R38
FINE_CURRENCY = "EUR"  # expect: R38
HOLD_SHELF_DAYS = 5

REFERENCE = "reference"  # expect-llm: R38
CIRCULATING = "circulating"  # expect-llm: R38
ARCHIVED = "archived"  # expect-llm: R38
