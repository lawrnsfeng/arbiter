# <pkg>/loans/loan_view.py
import click

from .messages import Msg


class LoanSheet:
    def __init__(self, record, *, include_fines: bool) -> None:
        self.record = record
        self.include_fines = include_fines

    def show(self) -> None:
        click.secho(Msg.LOANS_FOR(name=self.record.name), bold=True)
        for loan in self.record.loans:
            self.loan_line(loan)
        if self.include_fines:
            self.fines()

    def loan_line(self, loan) -> None:
        click.echo(Msg.LOAN_LINE(title=loan.title, due=loan.due))

    def fines(self) -> None:
        click.echo("Fines:")
        for fine in self.record.fines:
            click.echo(Msg.FINE_LINE(amount=fine.amount))


# <pkg>/loans/commands.py
@click.command()
@click.argument("member")
@click.option("--include-fines", is_flag=True)
def loans(member: str, *, include_fines: bool) -> None:
    LoanSheet(Member.lookup(member), include_fines=include_fines).show()


# look-alike: a private helper that computes, not prints
def _parse_member(raw: str) -> str:
    """Normalise a member id typed on the command line."""
    return raw.strip().lower()


def _echo_done() -> None:
    """Confirm a finished command."""
    click.echo("Done.")
