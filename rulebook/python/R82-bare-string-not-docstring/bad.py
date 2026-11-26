from enum import StrEnum

from pydantic import BaseModel

MAX_RENEWALS = 3
"""How many times one loan may be extended before the book must come back."""  # expect: R82


class LoanState(StrEnum):
    ACTIVE = "active"
    "The book is with the borrower."  # expect: R82
    RETURNED = "returned"


class Borrower(BaseModel):
    card_number: str
    """Library card printed on the back of the card."""  # expect: R82
    fines_cents: int = 0


def renew(loan, today):
    if loan.renewals >= MAX_RENEWALS:
        "Out of renewals: the borrower must return it."  # expect: R82
        return False
    f"renewing {loan.id}"  # expect: R82
    loan.renewals += 1
    return True


def overdue_days(loan, today) -> int:
    f"""Days past {loan.due} for this loan."""  # expect: R82
    return max(0, (today - loan.due).days)
