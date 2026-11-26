"""Imagine this module is `library/catalog/views.py`; the shared helper lives in `library/utils/dates.py`."""

from datetime import date

from library.utils.dates import due_label


class LoanView:
    def label(self, due: date, today: date) -> str:
        return due_label(due, today)


class HoldView:
    def label(self, due: date, today: date) -> str:
        return due_label(due, today)


class Book:
    def __init__(self, title: str) -> None:
        self.title = title

    def __str__(self) -> str:
        return self.title


class Journal:
    def __init__(self, title: str) -> None:  # tiny identical bodies are idioms, not copied helpers
        self.title = title

    def __str__(self) -> str:
        return self.title
