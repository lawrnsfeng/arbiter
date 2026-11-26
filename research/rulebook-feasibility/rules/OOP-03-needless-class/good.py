from dataclasses import dataclass


def greet(name: str) -> str:
    return f"hi {name}"


class Counter:  # holds state across calls: a real object
    def __init__(self) -> None:
        self.n = 0

    def inc(self) -> None:
        self.n += 1

    def value(self) -> int:
        return self.n


class Handler(Base):  # subclass: part of a hierarchy
    def __init__(self, x) -> None:
        self.x = x

    def handle(self) -> None:
        pass


@dataclass
class Point:
    x: int
    y: int


class Base: ...
