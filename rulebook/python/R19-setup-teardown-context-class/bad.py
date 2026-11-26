import os
import shutil
import tempfile
from contextlib import contextmanager

TEMPLATE = "/srv/recipes/template"


@contextmanager
def claimed_printer(device: "Printer"):  # expect: R19
    device.claim()
    try:
        yield device
    finally:
        device.release()


def print_card(device: "Printer", card: str) -> None:
    with claimed_printer(device) as printer:
        printer.reset()
        printer.select_tray("cards")
        printer.feed(card)


def print_menu(device: "Printer", pages: list[str]) -> None:
    with claimed_printer(device) as printer:
        printer.reset()
        printer.select_tray("a4")
        for page in pages:
            printer.feed(page)


@contextmanager
def scratch_kitchen():  # expect: R19
    workdir = tempfile.mkdtemp()
    try:
        yield workdir
    finally:
        shutil.rmtree(workdir)


def test_bake(oven) -> None:
    with scratch_kitchen() as kitchen:
        shutil.copytree(TEMPLATE, kitchen, dirs_exist_ok=True)
        os.chdir(kitchen)
        oven.bake("bread")


def test_chill(fridge) -> None:
    with scratch_kitchen() as kitchen:
        shutil.copytree(TEMPLATE, kitchen, dirs_exist_ok=True)
        os.chdir(kitchen)
        fridge.chill("custard")


def weigh(scale: "Scale") -> float:
    scale.power_on()  # expect-llm: R19
    try:
        return scale.read_grams()
    finally:
        scale.power_off()
