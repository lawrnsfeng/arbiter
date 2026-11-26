import click

LEGEND = "on loan:  checked out by a member\non hold:  waiting at the desk\nlost:     reported missing"


def usage() -> None:
    click.echo(
        "Commands:\n"
        "  checkout  Lend a book to a member\n"
        "  return    Take a book back\n"
        "  reserve   Hold a book for later\n"
    )


def rows(items: list[tuple[str, str]]) -> str:
    width = max(len(title) for title, _ in items) + 1
    return "\n".join(f"{title + ':':<{width}} {due}" for title, due in items)


# look-alike: single-space `key: value` text is data, not a padded table
CONFIG_SAMPLE = "branch: north\nopening_hours: 9-17\n"


def renew(loan, days: int) -> None:
    """Renew a loan.

    Args:
        loan:  the loan to renew
        days: how many days to add
    """
