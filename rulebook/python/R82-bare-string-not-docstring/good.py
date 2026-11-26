"""Loan renewal rules for the branch library."""

from enum import StrEnum, auto
from typing import Annotated

from pydantic import Field
from pydantic.dataclasses import dataclass

MAX_RENEWALS_BEFORE_RETURN = 3
OVERDUE_NOTICE: Annotated[str, Field(description="Text printed on the overdue slip.")] = "Please return this book."


class LoanState(StrEnum):
    """ACTIVE: the book is with the borrower. RETURNED: the book is back on the shelf."""

    ACTIVE = auto()
    RETURNED = auto()


@dataclass(frozen=True)
class Borrower:
    """A card holder; `fines_cents` is the unpaid total in cents."""

    card_number: str = Field(description="Library card printed on the back of the card.")
    fines_cents: int = 0


def renew(loan, today):
    """Extend the loan unless it is out of renewals."""
    if loan.renewals >= MAX_RENEWALS_BEFORE_RETURN:
        return False
    loan.renewals += 1
    return True


async def notice(loan) -> str:
    """Slip text for an overdue loan."""
    message: str = f"{OVERDUE_NOTICE} ({loan.id})"
    return message
