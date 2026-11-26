from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict


@dataclass(frozen=True)
class Ingredient:
    recipe_id: int
    servings: int
    name: str
    grams: float
    optional: bool = False


class RecipeImporter:
    def __init__(self, recipe_id: int, servings: int) -> None:
        self.recipe_id = recipe_id
        self.servings = servings

    def dough(self) -> Ingredient:
        return Ingredient(self.recipe_id, self.servings, "flour", 500.0)  # expect: R65

    def leaven(self, grams: float) -> Ingredient:
        return Ingredient(self.recipe_id, self.servings, "yeast", grams)  # expect: R65

    def topping(self, seed: str) -> Ingredient:
        return Ingredient(self.recipe_id, self.servings, seed, 5.0, optional=True)  # expect: R65


@dataclass(frozen=True)
class Seat:
    row: int
    letter: str
    flight: str
    cabin: str


def window_seats(flight: str, cabin: str, rows: range) -> dict[str, Seat]:
    first, last = rows[0], rows[-1]
    return {
        "front-left": Seat(first, "A", cabin=cabin, flight=flight),  # expect: R65
        "front-right": Seat(first, "F", flight=flight, cabin=cabin),  # expect: R65
        "rear-left": Seat(last, "A", flight=flight, cabin=cabin),  # expect: R65
    }


FLIGHT = "LX318"
CABIN = "economy"


def aisle_seat(row: int) -> Seat:
    return Seat(row, "C", FLIGHT, CABIN)  # expect: R65


def middle_seat(row: int) -> Seat:
    return Seat(row, "B", FLIGHT, CABIN)  # expect: R65


def window_seat(row: int) -> Seat:
    return Seat(row, "A", FLIGHT, CABIN)  # expect: R65


class Tag(BaseModel):
    model_config = ConfigDict(frozen=True)
    shelf: str
    colour: str
    text: str


def shelf_tags(shelf: str, colour: str) -> tuple[Tag, Tag, Tag]:
    new = Tag(shelf=shelf, colour=colour, text="new arrival")  # expect-llm: R65
    staff = Tag(shelf=shelf, colour=colour, text="staff pick")
    last = Tag(shelf=shelf, colour=colour, text="last copy")
    return new, staff, last
