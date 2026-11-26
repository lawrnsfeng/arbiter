from collections.abc import Callable, Iterator
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class Substitution[T]:
    original: T
    replacement: T


@dataclass(frozen=True)
class Substitutions[T]:
    items: tuple[Substitution[T], ...]

    @classmethod
    def from_tuples(cls, *pairs: tuple[T, T]) -> Self:
        return cls(tuple(Substitution(a, b) for a, b in pairs))

    def __iter__(self) -> Iterator[Substitution[T]]:
        return iter(self.items)

    def confirm(self, ask: Callable[[Substitution[T]], bool]) -> bool:
        return all(ask(s) for s in self)

    @property
    def summary(self) -> str:
        return ", ".join(f"{s.original} -> {s.replacement}" for s in self)


# look-alike: a single function over the records
def count_swaps(subs: list[Substitution[str]]) -> int:
    return len(subs)


# look-alikes: lists of plain values
def total_grams(weights: list[int]) -> int:
    return sum(weights)


def longest(names: list[str]) -> str:
    return max(names, key=len)


# look-alike: a list subclass of plain values, unrelated to the records
class Steps(list[str]):
    pass
