from library.membership import Tier


def shelve(index, scanner, journal, book) -> None:
    match book.section:
        case "fiction":
            shelve_by_author(index, scanner, journal, book, book.author)  # expect: R71
        case _:
            shelve_by_code(index, scanner, journal, book, book.call_number)  # expect: R71


def month_end(store, renderer, archive, period) -> None:
    export_report(store, renderer, archive, period, fmt="csv", compress=False)  # expect: R71


def year_end(store, renderer, archive, period) -> None:
    export_report(store, renderer, archive, period, fmt="pdf", compress=True)  # expect: R71


class Checkout:
    def quote(self, catalogue, tariff, rates, basket, member) -> float:
        if member.gold:
            return self.price(catalogue, tariff, rates, basket, Tier.GOLD)  # expect: R71
        return self.price(catalogue, tariff, rates, basket, Tier.STANDARD)  # expect: R71


def on_reserve(ledger, clock, desk, hold) -> None:  # expect-llm: R71
    desk.enqueue(ledger, clock, hold, "reserved")  # expect: R71


def on_release(ledger, clock, desk, hold) -> None:
    desk.enqueue(ledger, clock, hold, "released")  # expect: R71
