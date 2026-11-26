# ruff: noqa: ARG001  # expect: R15
import signal

import click


class ShelfCommand(click.Command):
    def format_help(self, ctx, formatter):  # noqa: ARG002  # expect: R15
        formatter.write_text("Shelve returned books.")


def on_return(book, event, when):  # pragma: no cover  # noqa: ARG001  # expect: R15
    book.shelve()


def on_alarm(signum, frame):  # expect-llm: R15
    print("loan desk closing", signum)


signal.signal(signal.SIGALRM, on_alarm)
