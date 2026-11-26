from dataclasses import dataclass


@dataclass(frozen=True)
class Ingredient:
    name: str
    grams: float


class Any:
    """A recipe tag meaning 'any cuisine'; unrelated to typing.Any."""


def has_nuts(ingredients: list[Ingredient]) -> bool:
    return any(i.name.endswith("nut") for i in ingredients)


def tag_of(label: str) -> Any:
    return Any() if label == "Any" else None


def describe(value: object) -> str:
    return str(value)
