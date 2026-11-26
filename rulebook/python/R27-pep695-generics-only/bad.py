import typing
from collections.abc import Callable
from typing import Generic, ParamSpec, Protocol, TypeVar

K = TypeVar("K")  # expect: R27
R = typing.TypeVar("R")  # expect: R27
P = ParamSpec("P")  # expect: R27


class Shelf(Generic[K]):  # expect: R27
    def __init__(self) -> None:
        self.slots: list[K] = []


class Source(Protocol[K]):  # expect: R27
    def next_item(self) -> K: ...


def logged(fn: Callable[P, R]) -> Callable[P, R]:
    return fn


class Change:
    before: object  # expect-llm: R27
    after: object
