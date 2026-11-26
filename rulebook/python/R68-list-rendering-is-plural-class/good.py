import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Loan:
    title: str


@dataclass(frozen=True)
class Loans:
    items: tuple[Loan, ...]

    @property
    def notice(self) -> str:
        return "Overdue: " + "; also ".join(loan.title for loan in self.items)


def overdue_notice(loans: list[Loan]) -> str:
    return Loans(tuple(loans)).notice


def later_stops(stops) -> str:
    first: object = stops[0]
    print(first)
    return ", ".join(s.name for s in stops[1:])


def command_line() -> str:
    return sys.argv[0] + " " + " ".join(sys.argv[1:])


def gaps(readings) -> str:
    return " ".join(str(r.value - readings[0].value) for r in readings[1:])

def table(rows) -> tuple[str, str]:
    header: str = rows[0].cells
    body: str = "\n".join(r.line for r in rows[1:])
    return header, body



def tail(stops) -> list:
    return stops[1:] + [stops[0]]
