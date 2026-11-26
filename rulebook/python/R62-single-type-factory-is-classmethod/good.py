from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Protocol, Self


@dataclass(frozen=True)
class Loan:
    isbn: str
    member: str
    due: date

    @classmethod
    def from_isbn(cls, isbn: str, member: str, days: int) -> Self:
        return cls(isbn, member, date.today() + timedelta(days=days))

    def extend(self, days: int) -> "Loan":
        return Loan(self.isbn, self.member, self.due + timedelta(days=days))


class Lender(Protocol):
    def lend(self, isbn: str) -> Loan:
        """Lend the copy with this ISBN to the current member."""


def due_dates(rows: list[dict]) -> list[date]:
    return [date.fromisoformat(r["due"]) for r in rows]


def parse_due(text: str) -> date:
    return date.fromisoformat(text.strip())


def lookup(index: Mapping[str, Loan], isbn: str) -> Loan | None:
    return index.get(isbn)


def default_lender() -> Lender:
    return LocalLender()
