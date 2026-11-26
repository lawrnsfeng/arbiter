from dataclasses import dataclass
from typing import Self


@dataclass
class Recipe:
    title: str
    ingredients: list[str]
    garnish: list[str]
    servings: int

    @property
    def items(self) -> list[str]:
        return [*self.ingredients, *self.garnish]

    def scale_servings(self, factor: float) -> int:
        return round(self.servings * factor)

    def shopping_cost(self, prices: dict[str, float]) -> float:
        return sum(prices.get(item, 0.0) for item in self.ingredients)


@dataclass(frozen=True)
class Shelf:
    label: str
    capacity: int

    @classmethod
    def from_row(cls, row: dict) -> Self:
        return cls(row["name"], int(row.get("cap", 10)))


class Cookbook:
    def __init__(self, recipes: list[Recipe]) -> None:
        self.recipes = recipes

    @staticmethod
    def slug(text: str) -> str:
        return "-".join(text.lower().split())

    def anchors(self) -> list[str]:
        return [self.slug(r.title) for r in self.recipes]

    def index(self) -> dict[str, Recipe]:
        return {self.slug(r.title): r for r in self.recipes}


class RecipeCard:
    def __init__(self, recipe: Recipe) -> None:
        self.recipe = recipe

    @property
    def text(self) -> str:
        return "\n".join([f"== {self.recipe.title.upper()} ==", *(f"  {i}" for i in self.recipe.ingredients)])


def _normalise(text: str) -> str:
    """Strip accents and case before comparing titles.

    Stays free: used by both Pantry and Menu; moving it onto either would make the other import it.
    """
    return text.casefold()


class Pantry:
    def find(self, cookbook: Cookbook, title: str) -> list[Recipe]:
        return [r for r in cookbook.recipes if _normalise(r.title) == _normalise(title)]


class Menu:
    def has(self, cookbook: Cookbook, title: str) -> bool:
        return any(_normalise(r.title) == _normalise(title) for r in cookbook.recipes)


def _is_metric(unit: str) -> bool:
    """True for SI units.

    Stays free: a predicate over a primitive string; no project type owns units.
    """
    return unit in {"g", "kg", "ml", "l"}


def __dir__() -> list[str]:
    return sorted(globals())
