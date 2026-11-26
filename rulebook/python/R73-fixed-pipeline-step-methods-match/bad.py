from enum import IntEnum, StrEnum


class Stage(StrEnum):
    MEASURE = "measure"
    LABEL = "label"
    LOAD = "load"


class Phase(IntEnum):
    MEASURE = 1
    LABEL = 2

    def label(self) -> str:  # expect: R73
        return self.name.lower()

    @classmethod
    def parse(cls, text: str) -> "Phase":  # expect: R73
        return cls[text.upper()]


def needs_refresh(fn):
    fn.refresh = True  # expect: R73
    return fn


def measure(parcel) -> None:
    parcel.grams = parcel.scale.read()
    parcel.db.save(stage="measure")  # expect-llm: R73


@needs_refresh
def label(parcel) -> None:
    parcel.printer.print(parcel.code)  # type: ignore[attr-defined]  # expect-llm: R73


def load(parcel) -> None:
    parcel.van.add(parcel)


load.refresh = True  # expect: R73

PIPELINE = (measure, label, load)
HANDLERS = {"measure": measure, "label": label, "load": load}


def process(parcel, current: Stage) -> None:
    if current > Stage.LABEL:  # expect: R73
        return
    for stage_fn in PIPELINE:  # expect: R73
        stage_fn(parcel)


def resume(parcel, name: str) -> None:
    HANDLERS[name](parcel)  # expect: R73
    for key, handler in HANDLERS.items():  # expect: R73
        handler(parcel)
