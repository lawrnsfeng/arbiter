import pytest


class UnknownShelf(ValueError): ...


def lend(catalog, ledger, shelves: list[str], member: str) -> None:
    for code in shelves:
        ledger.record(member, code)
        if code not in catalog:
            raise UnknownShelf(code)  # expect-llm: R88


def notify(member, channel: str, fine_cents: int) -> None:
    if fine_cents > 10_000:  # expect-llm: R88
        raise ValueError("fine over cap")
    if channel == "email":
        send_email(member.address, "Your book is due")
    else:
        send_letter(member.address, f"Fine due: {fine_cents}")


def test_lend_unknown_shelf(catalog, ledger) -> None:  # expect-llm: R88
    with pytest.raises(UnknownShelf):
        lend(catalog, ledger, ["Z9"], "m-1")


def handle_webhook(body: bytes) -> dict:
    try:
        return json.loads(body)
    except ValueError:
        return {"error": "malformed"}  # expect-llm: R88
