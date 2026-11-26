"""Imagine this module is `library/catalog/views.py`, in the catalog subsystem of a `library` package."""

from datetime import date

from library.loans.calendar import business_days  # expect-llm: R54


class LoanView:
    def due_label(self, due: date, today: date) -> str:
        days = (due - today).days
        if days < 0:
            return f"{-days} days overdue"
        return f"due in {days} days"


class HoldView:
    def due_label(self, due: date, today: date) -> str:  # expect: R54
        days = (due - today).days
        if days < 0:
            return f"{-days} days overdue"
        return f"due in {days} days"


def pickup_label(due, today):  # expect: R54
    """Same helper, copied and renamed for the pickup shelf."""
    days = (due - today).days
    if days < 0:
        return f"{-days} days overdue"
    return f"due in {days} days"


def opening_hours_left(now, closing):
    return business_days(now, closing)
