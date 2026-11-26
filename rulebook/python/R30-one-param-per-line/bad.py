class Kitchen:
    def schedule(  # expect: R30
        self, recipe: str, servings: int = 2, oven_c: int | None = None
    ) -> "Plan":
        return Plan(recipe, servings, oven_c)

    def plate(self, dish: str,  # expect: R30
              garnish: str | None = None) -> str:
        return dish


def scale(  # expect: R30
    recipe: str,
    factor: float,
    *,
    round_to: int = 1
) -> str:
    return recipe


async def preheat(  # expect: R30
    oven: str,
    target_c: int, minutes: int,
) -> None:
    return None
