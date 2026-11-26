import signal

import click


class ShelfCommand(click.Command):
    # ctx stays: click passes it positionally to format_help; ARG002 is ignored for this file in the ruff config
    def format_help(self, ctx, formatter):
        formatter.write_text("Shelve returned books.")


def on_alarm(signum, _frame, /):  # pragma: no cover
    print("loan desk closing", signum)


signal.signal(signal.SIGALRM, on_alarm)

HELP = "silence ARG002 in pyproject per-file-ignores, not with  # noqa: ARG002"
