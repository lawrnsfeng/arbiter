import json
from pathlib import Path


def ledger_size(path: str) -> int:
    with open(path) as fh:
        data = json.load(fh)  # expect: R20
    return len(data)


def card_title(card: Path) -> str:
    contents: str = card.read_text()  # expect: R20
    return contents.splitlines()[0]


def total(batches: list[list[int]]) -> int:
    count = 0
    for data in batches:  # expect: R20
        count += len(data)
    return count


def first_line(p: Path) -> str:
    with open(p) as contents:  # expect: R20
        return contents.readline()


class Pantry:
    contents: list[str]  # expect: R20

    def __init__(self) -> None:
        self.data = {}  # expect: R20


def parse(body: bytes) -> dict:
    payload = json.loads(body)  # expect-llm: R20
    return payload
