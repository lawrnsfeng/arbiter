import pytest

MAX_TITLES = 5
MIN_DAYS, MAX_DAYS = 1, 28
MAX_LETTER_FINE_CENTS = 10_000


class UnknownShelf(ValueError):
    """A shelf code the catalog does not hold."""


class EmptySelection(ValueError):
    """No shelf chosen: absent or an empty list."""


class LoanLength(ValueError):
    """A loan length outside the allowed day range."""


class FineOverCap(ValueError):
    """A fine above what a letter may print."""


class ShelfCodeType(TypeError):
    """A selection that is not a list of shelf-code strings."""


class TooManyTitles(ValueError):
    """More titles than one loan may carry."""


def lend(catalog, ledger, member: str, shelves: list[str] | None = None, days: int = 14) -> None:
    if not shelves:
        raise EmptySelection(member)
    if not isinstance(shelves, list) or not all(isinstance(c, str) for c in shelves):
        raise ShelfCodeType(shelves)
    if len(shelves) > MAX_TITLES:
        raise TooManyTitles(len(shelves))
    if not MIN_DAYS <= days <= MAX_DAYS:
        raise LoanLength(days)
    if unknown := [c for c in shelves if c not in catalog]:
        raise UnknownShelf(unknown)
    for code in shelves:
        ledger.record(member, code, days)


@pytest.mark.parametrize(
    ("shelves", "days", "error"),
    [
        (None, 14, EmptySelection),  # absent
        ([], 14, EmptySelection),  # empty
        ("A1", 14, ShelfCodeType),  # wrong type
        ([1], 14, ShelfCodeType),  # wrong element type
        (["Z9"], 14, UnknownShelf),  # unknown member
        (["A1"] * (MAX_TITLES + 1), 14, TooManyTitles),  # over the title bound
        (["A1"], MIN_DAYS - 1, LoanLength),  # under the day bound
        (["A1"], MAX_DAYS + 1, LoanLength),  # over the day bound
    ],
)
def test_lend_refuses(catalog, ledger, shelves, days, error) -> None:
    with pytest.raises(error):
        lend(catalog, ledger, "m-1", shelves, days)
    assert ledger.records == []


def test_lend_default_selection_is_refused_and_not_shared(catalog, ledger) -> None:
    with pytest.raises(EmptySelection):
        lend(catalog, ledger, "m-1")
    assert lend.__defaults__ == (None, 14)
    assert ledger.records == []


def notify(member, channel: str, fine_cents: int, outbox) -> None:
    if channel == "email":
        outbox.email(member.address, "Your book is due")
        return
    if fine_cents > MAX_LETTER_FINE_CENTS:  # only the letter prints the fine, so only the letter checks it
        raise FineOverCap(fine_cents)
    outbox.letter(member.address, f"Fine due: {fine_cents}")


def test_email_ignores_fine(member, outbox) -> None:
    notify(member, "email", MAX_LETTER_FINE_CENTS * 5, outbox)
    assert outbox.sent == ["email"]


def test_letter_refuses_fine_over_cap(member, outbox) -> None:
    with pytest.raises(FineOverCap):
        notify(member, "letter", MAX_LETTER_FINE_CENTS + 1, outbox)
    assert outbox.sent == []


def late_days(due, returned) -> int:
    return max(0, (returned - due).days)


def test_late_days() -> None:
    assert late_days(date(2026, 1, 1), date(2026, 1, 4)) == 3
