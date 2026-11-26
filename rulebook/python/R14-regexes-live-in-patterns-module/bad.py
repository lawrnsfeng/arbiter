import re
from re import compile as rx

# matches "SHELF 12-B"
SHELF_CODE = re.compile(r"SHELF (\d+)-([A-Z])")  # expect: R14
ISBN = re.compile(r"\d{3}-\d{10}")  # expect: R14


def shelf_of(label):
    found = SHELF_CODE.search(label)
    return found.groups() if found else None


def due_dates(text):
    stamp = re.compile(r"due (\d{4}-\d{2}-\d{2})")  # expect: R14
    return stamp.findall(text)


class CardReader:
    CARD = rx(r"CARD-(\d{6})")  # expect: R14

    def card_number(self, raw):
        return self.CARD.match(raw)


def is_overdue(note):
    return re.search(r"overdue since \d+ days", note) is not None  # expect-llm: R14
