import logging

import click

log = logging.getLogger(__name__)


# <pkg>/loans/messages.py
class Template(str):
    def __call__(self, **values: object) -> str:
        return self.format(**values)


class Messages:
    FINE_DUE: Template = Template("{member} owes {amount:.2f} in fines")
    DUE_BACK: Template = Template("Due back {due:%d %b}: {title!r}")


Msg = Messages


# <pkg>/loans/commands.py
def show_fine(member, amount):
    click.echo(Msg.FINE_DUE(member=member.name, amount=amount))


def show_due(loan):
    click.echo(Msg.DUE_BACK(title=loan.title, due=loan.due))


# look-alikes: no interpolation, logging, and `.format` outside an output call
def done():
    click.echo("Done.")
    click.echo(f"plain text")
    log.info(f"sent {3} reminders")
    return "/loans/{}".format(7)
