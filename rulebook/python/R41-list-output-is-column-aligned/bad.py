import click

LEGEND = "on loan:   checked out by a member\non hold:  waiting at the desk\nlost:     reported missing"  # expect: R41


def usage() -> None:
    click.echo(
        "Commands:\n"  # expect: R41
        "  checkout   Lend a book to a member\n"
        "  return  Take a book back\n"
        "  reserve     Hold a book for later\n"
    )


def summary(loans: int, holds: int) -> str:
    return f"loans:  {loans}\nholds on shelf: {holds}"  # expect: R41


def rows(items: list[tuple[str, str]]) -> str:
    return "\n".join(f"{title}: {due}" for title, due in items)  # expect-llm: R41
