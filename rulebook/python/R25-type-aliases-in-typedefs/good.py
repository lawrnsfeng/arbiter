from recipes.typedefs import Ingredient, NutritionRow, Pantry

DEFAULT_UNITS = ("g", "ml")
READ = 1
WRITE = 2
READ_WRITE = READ | WRITE


def shopping_list(pantry: Pantry) -> list[str]:
    return sorted(pantry)


def nutrition(recipe: str) -> NutritionRow:
    return NutritionRow(recipe, "kcal", 0, 0.0)


# Look-alikes: two levels, a variadic tuple, a three-member tuple.
def tags(recipe: str) -> dict[str, list[int]]:
    return {recipe: []}


def timings(recipe: str) -> tuple[int, ...]:
    return ()


def summary(ingredient: Ingredient) -> tuple[str, float, str]:
    return "", 0.0, ""
