def loan_summary(loans):
    overdue = sum(1 for loan in loans if loan.is_overdue)  # expect: R48
    returned = sum(1 for loan in loans if loan.returned_at)  # expect: R48
    fines = sum(loan.fine for loan in loans)  # expect: R48
    return overdue, returned, fines


def shelf_report(shelf):
    novels = len([b for b in shelf.books if b.genre == "novel"])  # expect: R48
    poetry = len([b for b in shelf.books if b.genre == "poetry"])  # expect: R48
    return novels, poetry


def genre_tally(genres: list[str]) -> tuple[int, int]:
    return genres.count("novel"), genres.count("poetry")  # expect: R48


def branch_pages(branches):
    for branch in branches:
        lent = sum(b.pages for b in branch.books if b.on_loan)  # expect: R48
        kept = sum(b.pages for b in branch.books if not b.on_loan)  # expect: R48
        yield branch.name, lent, kept
