# <pkg>/loans/commands.py
import click


@click.command()
@click.argument("member")
@click.option("--verbose", is_flag=True)
def loans(member: str, verbose: bool) -> None:
    record = Member.lookup(member)
    _loan_header(record)
    for loan in record.loans:
        _loan_row(loan)
    if verbose:
        _fine_section(record)


def _loan_header(record) -> None:  # expect: R44
    click.secho(f"Loans for {record.name}", bold=True)


def _loan_row(loan) -> None:  # expect: R44
    click.echo(f"  {loan.title:<30} due {loan.due:%d %b}")


def _fine_section(record) -> None:  # expect: R44
    print("Fines:")
    for fine in record.fines:
        print(f"  {fine.amount:.2f}")


def cmd_holds(member: str) -> None:  # expect-llm: R44
    """Thick command: renders rows itself instead of dispatching to a view."""
    record = Member.lookup(member)
    for hold in record.holds:
        click.echo(f"{hold.title} at position {hold.position}")
    if click.confirm("Cancel all?"):
        record.cancel_holds()
