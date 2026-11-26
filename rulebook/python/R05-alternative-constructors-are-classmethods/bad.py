import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Loan:
    book: str
    member: str
    days: int


def load_loan(path: Path) -> Loan:  # expect: R5
    data = json.loads(path.read_text())
    return Loan(data["book"], data["member"], data["days"])


def _loan_from_row(row) -> "Loan":  # expect: R5
    return Loan(*row)


class Member:
    def __init__(self, card, name):
        self.card = card
        self.name = name

    @classmethod
    def parse(cls, line):  # expect: R5
        card, name = line.split(",")
        return cls(card.strip(), name.strip())

    @classmethod
    def create(cls, record: dict[str, str]) -> "Member":  # expect: R5
        return cls(record["card"], record["name"])


def member_for_card(card):  # expect-llm: R5
    member = Member.__new__(Member)
    member.card = card
    member.name = "unknown"
    return member
