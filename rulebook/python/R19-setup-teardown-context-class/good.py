import time
from contextlib import contextmanager
from typing import Self


class PrintJob:
    """A claimed printer, reset and loaded from one tray for the length of a job."""

    def __init__(self, device: "Printer", tray: str) -> None:
        self._device = device
        self._tray = tray

    def __enter__(self) -> Self:
        self._device.claim()
        self._device.reset()
        self._device.select_tray(self._tray)
        return self

    def print_page(self, page: str) -> None:
        self._device.feed(page)

    def __exit__(self, *exc: object) -> None:
        self._device.release()


def print_menu(device: "Printer", pages: list[str]) -> None:
    with PrintJob(device, "a4") as job:
        for page in pages:
            job.print_page(page)


# Look-alike: the callers do unrelated work inside the block.
@contextmanager
def timed(label: str):
    start = time.monotonic()
    try:
        yield start
    finally:
        print(label, time.monotonic() - start)


def simmer(pot) -> None:
    with timed("simmer") as started:
        pot.heat(since=started)


def plate(dish, out) -> None:
    with timed("plate") as started:
        out.write(dish.describe(started))
