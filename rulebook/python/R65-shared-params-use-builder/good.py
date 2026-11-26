from dataclasses import dataclass


@dataclass(frozen=True)
class Ingredient:
    recipe_id: int
    servings: int
    name: str
    grams: float
    is_optional: bool = False


class IngredientBuilder:
    def __init__(self, recipe) -> None:
        self._recipe_id = recipe.id
        self._servings = recipe.servings

    def build(self, name: str, grams: float, *, is_optional: bool = False) -> Ingredient:
        return Ingredient(self._recipe_id, self._servings, name, grams, is_optional)


def pantry(recipe) -> list[Ingredient]:
    make: IngredientBuilder = IngredientBuilder(recipe)
    return [make.build("flour", 500.0), make.build("yeast", 7.0), make.build("sesame", 5.0, is_optional=True)]


@dataclass(frozen=True)
class Span:
    start: int
    end: int

    @property
    def minutes(self) -> int:
        return self.end - self.start


def morning_minutes(start: int, end: int) -> int:
    return Span(start, end).minutes


def afternoon_minutes(start: int, end: int) -> int:
    return Span(start, end).minutes


def evening_minutes(start: int, end: int) -> int:
    return Span(start, end).minutes


def corners(a: int, b: int, c: int) -> list[Span]:
    return [Span(a, 0), Span(b, 0), Span(c, 0)]
