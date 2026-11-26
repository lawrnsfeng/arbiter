from dataclasses import dataclass
from datetime import date, timedelta
from functools import cache

from .stock import Shelf as StockShelf


@dataclass(frozen=True)
class Loan:
    isbn: str
    member: str
    due: date


@dataclass(frozen=True)
class Shelf:
    code: str


def loan_for(isbn: str, member: str, days: int) -> Loan:  # expect: R62
    return Loan(isbn, member, date.today() + timedelta(days=days))


def _shelf_from_label(label: str) -> "Shelf":  # expect: R62
    return Shelf(label.split("-")[0].upper())


async def loan_from_row(row: dict) -> Loan:  # expect: R62
    return Loan(row["isbn"], row["member"], date.fromisoformat(row["due"]))


def restock(code: str) -> StockShelf:  # expect: R62
    return StockShelf(code)


@cache
def default_shelf() -> Shelf:  # expect-llm: R62
    return Shelf("A")
