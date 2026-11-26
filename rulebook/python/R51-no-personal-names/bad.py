import csv
import io

__author__ = "Margaret Hamilton"  # expect-llm: R51

SEED_MEMBERS = [
    {"card": "C-001", "holder": "Grace Hopper", "tier": "staff"},  # expect-llm: R51
    {"card": "C-002", "holder": "member two", "tier": "public"},
]


def load_members(text: str) -> list[dict[str, str]]:
    # Ask bob before changing the fine schedule; he signs off every change.  # expect-llm: R51
    return list(csv.DictReader(io.StringIO(text)))


def test_ada_can_borrow_ten_books(library):  # expect-llm: R51
    assert library.limit_for("C-001") == 10
