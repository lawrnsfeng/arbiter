import json
from dataclasses import dataclass
from pathlib import Path

import pytest


@dataclass(frozen=True)
class Loan:
    book: str
    member: str
    days: int

    @classmethod
    def from_json_file(cls, path: Path) -> "Loan":
        loan_record = json.loads(path.read_text())
        return cls(loan_record["book"], loan_record["member"], loan_record["days"])


class Member:
    def __init__(self, card: str, name: str) -> None:
        self.card = card
        self.name = name

    @classmethod
    def from_csv_line(cls, line: str) -> "Member":
        card, name = line.split(",")
        return cls(card.strip(), name.strip())

    @classmethod
    def anonymous(cls) -> "Member":
        return cls("0000", "anonymous")


@pytest.fixture
def overdue_loan() -> Loan:
    return Loan("Dune", "ana", 40)


def archive_dir(root: str) -> Path:
    return Path(root) / "archive"


def latest_loan(folder: Path) -> Loan:
    return Loan.from_json_file(max(folder.glob("*.json")))


def first_loan(loans: list[Loan]) -> Loan:
    return loans[0]
