from pathlib import Path

from library.settings import RETURN_WINDOW_DAYS

MAX_RENEWALS = 3
HOLD_SHELF: Path = Path("/srv/holds")


def can_renew(loan, max_renewals: int | None = None) -> bool:  # expect: R60
    limit = max_renewals if max_renewals is not None else MAX_RENEWALS
    return loan.renewals < limit


def due_date(start, return_window_days=None):  # expect: R60
    return start.plus(days=return_window_days or RETURN_WINDOW_DAYS)


class Shelving:
    def place(
        self,
        book,
        hold_shelf: Path | None = None,  # expect: R60
    ) -> Path:
        return (hold_shelf or HOLD_SHELF) / book.code


def grace_end(start, window=None):
    days = window or RETURN_WINDOW_DAYS  # expect-llm: R60
    return start.plus(days=days)
