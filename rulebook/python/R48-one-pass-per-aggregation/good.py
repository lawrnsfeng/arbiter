from collections import Counter


def loan_summary(loans):
    overdue: int = 0
    returned: int = 0
    fines: float = 0.0
    for loan in loans:
        overdue += loan.is_overdue
        returned += loan.returned_at is not None
        fines += loan.fine
    return overdue, returned, fines


def shelf_report(shelf) -> Counter[str]:
    return Counter(b.genre for b in shelf.books)


def two_shelves(left, right) -> tuple[int, int]:
    return sum(b.pages for b in left.books), sum(b.pages for b in right.books)  # different sequences


def branch_totals(branches) -> int:
    total: int = sum(len(b.books) for b in branches)
    overdue: int = sum(map(lambda branch: sum(1 for book in branch.books if book.overdue), branches))  # own scope
    return total + overdue


def database_counts(loans_query, holds_query) -> tuple[int, int]:
    return loans_query.count(), holds_query.count()  # query counts, not passes over one sequence


def headline_total(loans, mode: str) -> float:
    if mode == "fines":  # exclusive branches: only one pass ever runs
        return sum(loan.fine for loan in loans)
    else:
        return sum(loan.deposit for loan in loans)


def renewals(loans, *, is_member: bool) -> int:
    if is_member:
        return sum(loan.renewals for loan in loans)
    return sum(1 for loan in loans if loan.renewed)  # after an early return: still one pass per call
