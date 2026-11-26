from enum import IntEnum, StrEnum
from typing import Self


class Stage(StrEnum):
    order: int

    def __new__(cls, value: str, order: int) -> Self:
        member: Self = str.__new__(cls, value)
        member._value_ = value
        member.order = order
        return member

    MEASURE = "measure", 1
    LABEL = "label", 2
    LOAD = "load", 3

    @property
    def next(self) -> "Stage | None":
        return next((s for s in Stage if s.order == self.order + 1), None)


class Priority(IntEnum):
    LOW = 1
    HIGH = 2

    def __str__(self) -> str:
        return self.name.title()


UNITS = ("kg", "lb")


class Onboarding:
    def __init__(self, parcel, db) -> None:
        self.parcel = parcel
        self.db = db

    def measure(self) -> None:
        self.parcel.grams = self.parcel.scale.read()

    def label(self) -> None:
        self.parcel.printer.print(self.parcel.code)

    def load(self) -> None:
        self.parcel.van.add(self.parcel)

    def run_stage(self, stage: Stage) -> Stage | None:
        match stage:
            case Stage.MEASURE:
                method, refresh = self.measure, False
            case Stage.LABEL:
                method, refresh = self.label, True
            case Stage.LOAD:
                method, refresh = self.load, False
        method()
        if refresh:
            self.parcel.reload()
        self.db.save(stage=stage.next)
        return stage.next

    def resume(self, row: dict) -> None:
        stage: Stage | None = Stage(row["stage"])
        while stage is not None and stage.order <= Stage.LOAD.order:
            stage = self.run_stage(stage)


def describe() -> list[str]:
    return [unit.upper() for unit in UNITS]


def cmd_weigh(args) -> None:
    print(args.parcel)


def cmd_label(args) -> None:
    print(args.parcel)


COMMANDS = {"weigh": cmd_weigh, "label": cmd_label}


def main(args) -> None:
    COMMANDS[args.cmd](args)
