from dataclasses import dataclass
from enum import StrEnum


class Stage(StrEnum):
    PROOF = "proof"
    BAKE = "bake"


@dataclass
class Loaf:
    recipe: str

    def advance(self, stage: Stage) -> None:
        method = getattr(self, f"run_{stage.value}")  # expect: R74
        method()

    def oven(self):
        if hasattr(self, "_oven"):  # expect: R74
            return self._oven
        self._oven = object()
        return self._oven

    @classmethod
    def preset(cls, name: str) -> "Loaf":
        return getattr(cls, name.upper())  # expect: R74

    def describe(self, kind: str) -> str:
        return getattr(type(self), kind)(self)  # expect: R74

    def glaze(self, finish: str) -> None:
        getattr(self.__class__, f"glaze_{finish}")(self)  # expect: R74

    def supports(self, tin: str) -> bool:
        return hasattr(Loaf, f"tin_{tin}")  # expect: R74


def heat(oven, mode: str) -> None:
    getattr(oven, mode)()  # expect-llm: R74
