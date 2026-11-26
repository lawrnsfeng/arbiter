import logging
from dataclasses import dataclass
from enum import StrEnum, auto


class Stage(StrEnum):
    PROOF = auto()
    BAKE = auto()


@dataclass
class Loaf:
    recipe: str

    def advance(self, stage: Stage) -> None:
        match stage:
            case Stage.PROOF:
                self.proof()
            case Stage.BAKE:
                self.bake()


class TraceFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return getattr(record, "trace_id", None) is not None


class OvenProxy:
    def __init__(self, inner) -> None:
        self._inner = inner

    def __getattr__(self, name: str):
        return getattr(self._inner, name)


def load_plugins(modules) -> list:
    return [hook for m in modules if (hook := getattr(m, "register", None))]
