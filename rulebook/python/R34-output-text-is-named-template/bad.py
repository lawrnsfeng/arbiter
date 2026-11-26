import click
from click import secho

from .messages import Msg


def show_due(loan):
    click.echo(f"Due back {loan.due:%d %b}: {loan.title!r}")  # expect: R34


def show_hold(title, position):
    secho("Hold placed on {} at position {}".format(title, position), fg="green")  # expect: R34


def show_fine(member, amount):
    click.echo(Msg.FINE_DUE(member.name, amount))  # expect: R34


def show_returned(count):
    print("Returned %d books" % count)  # expect: R34


def show_renewal(title, days):
    text = f"{title} renewed for {days} days"  # expect-llm: R34
    click.echo(text)
