from collections.abc import Callable
from typing import Protocol


class Shelf[K]:
    def __init__(self) -> None:
        self.slots: list[K] = []


class Source[K](Protocol):
    def next_item(self) -> K: ...


def logged[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    return fn


class Change[T]:
    before: T
    after: T


# Look-alikes: an unsubscripted Protocol base, a single object parameter, the word in a string.
class Closeable(Protocol):
    def close(self) -> None: ...


def describe(value: object) -> str:
    return "TypeVar" if value is None else repr(value)
