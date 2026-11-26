from pathlib import Path
from uuid import UUID

from library.settings import RETURN_WINDOW_DAYS

MAX_RENEWALS = 3
HOLD_SHELF: Path = Path("/srv/holds")


def can_renew(loan, limit: int) -> bool:
    return loan.renewals < limit


def due_date(start, window_days: int):
    return start.plus(days=window_days)


class Shelving:
    def place(self, book, shelf: Path) -> Path:
        return shelf / book.code


def find_loan(uuid: str) -> UUID:
    return UUID(uuid)


def renew(loan) -> bool:
    max_renewals: int = MAX_RENEWALS  # a local, not a parameter
    if can_renew(loan, MAX_RENEWALS):  # the caller reads the constant and passes it
        loan.due = due_date(loan.start, RETURN_WINDOW_DAYS)
        Shelving().place(loan.book, HOLD_SHELF)
    return max_renewals > 0


def newest[T](t: list[T], count: int = 1) -> list[T]:  # `t` beside the type parameter `T` is not a case-twin
    return t[-count:]
