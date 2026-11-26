import json
import re
from datetime import datetime

ISBN13 = re.compile(r"97[89]-(?P<group>\d{1,5})-(?P<rest>[\d-]+)")


def floor_number(shelf_mark: str) -> int:  # expect: R9
    floor, _, _bay = shelf_mark.partition("/")
    return int(floor.removeprefix("L"))


def isbn_group(isbn: str) -> str:  # expect: R9
    found = ISBN13.fullmatch(isbn)
    return found["group"] if found else ""


def slip_due(slip: str) -> datetime:  # expect: R9
    return datetime.strptime(slip, "DUE %Y%m%d")


def card_fields(card: bytes) -> dict:  # expect: R9
    return json.loads(card)


def branch_of(call_number: str) -> str:  # expect: R9
    return call_number[4:7]


class Desk:
    def can_lend(self, shelf_mark: str) -> bool:  # expect-llm: R9
        return shelf_mark.partition("/")[0] in self.open_floors

    def route(self, shelf_mark: str) -> str:  # expect-llm: R9
        return self.lifts[shelf_mark.partition("/")[0]]
