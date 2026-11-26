from collections.abc import Callable
from typing import NewType, TypeAlias

CourseList = list[tuple[str, int]]  # expect: R25
type Ingredient = dict[str, float]  # expect: R25
Scaler: TypeAlias = Callable[[float], float]  # expect: R25
RecipeId = NewType("RecipeId", int)  # expect: R25
MaybeServings = int | None  # expect: R25


def shopping_list(
    pantry: dict[str, list[tuple[str, float]]],  # expect: R25
) -> list[str]:
    return sorted(pantry)


def nutrition(recipe: str) -> tuple[str, str, int, float]:  # expect: R25
    return recipe, "kcal", 0, 0.0


def steps(
    recipe: str,
) -> dict[  # expect: R25
    str,
    list[str],
]:
    return {recipe: []}
