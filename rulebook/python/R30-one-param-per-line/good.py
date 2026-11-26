class Kitchen:
    def schedule(
        self,
        recipe: str,
        servings: int = 2,
        oven_c: int | None = None,
    ) -> "Plan":
        return Plan(recipe, servings, oven_c)

    # Look-alike: fits on one line.
    def plate(self, dish: str, garnish: str | None = None) -> str:
        return dish


def scale(
    recipe: str,
    factor: float,
    *,
    round_to: int = 1,  # keep one per line
) -> str:
    return recipe


# Look-alikes: a wrapped single parameter, and a return annotation that wraps.
def label(
    recipe_title_that_is_quite_long: str
) -> str:
    return recipe_title_that_is_quite_long


def courses(menu: str, day: int) -> dict[
    str,
    list[str],
]:
    return {}
