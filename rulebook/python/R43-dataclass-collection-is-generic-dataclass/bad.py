from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class Substitution:
    original: str
    replacement: str


def apply_all(subs: list[Substitution], recipe: str) -> str:  # expect: R43
    for sub in subs:
        recipe = recipe.replace(sub.original, sub.replacement)
    return recipe


def summarise(subs: Sequence[Substitution]) -> str:  # expect: R43
    return ", ".join(f"{s.original} -> {s.replacement}" for s in subs)


def confirm(subs: list[Substitution], ask) -> bool:  # expect: R43
    return all(ask(s) for s in subs)


class SubstitutionList(list[object]):  # expect: R43
    def apply(self, recipe: str) -> str: ...


class SubstitutionBatch(list[Substitution]):  # expect: R43
    pass


def plan(subs, recipe):  # expect-llm: R43
    """Unannotated: the same list is threaded through each free function."""
    if confirm(subs, input):
        return apply_all(subs, recipe)
    return recipe
